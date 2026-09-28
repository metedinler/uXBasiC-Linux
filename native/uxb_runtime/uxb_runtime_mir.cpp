#include "uxb_runtime.h"
#include "uxb_runtime_state.h"
#include "uxb_runtime_print.h"

#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <mutex>
#include <random>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#if defined(_WIN32)
#include <conio.h>
#include <windows.h>
#endif

namespace {

thread_local std::array<std::string, 32> text_ring;
thread_local std::size_t text_ring_index = 0;
std::mutex file_mutex;
std::unordered_map<int64_t, std::FILE*> files;
std::mutex random_mutex;
std::mt19937_64 random_engine{0x55584241534943ULL};

const char* hold_text(std::string value) {
    std::string& slot = text_ring[text_ring_index++ % text_ring.size()];
    slot = std::move(value);
    return slot.c_str();
}

// S-157: STRING DEGISKENLERININ SAHIPLI DEPOSU. Metin ureten fonksiyonlar sonucu yukaridaki is
// parcacigina ozel 32 yuvalik halkaya yazar (gecici deger). Bir degiskene / dizi elemanina / alana
// yazilan metin eskiden halkayi gosteriyordu ve 32 metin isleminden sonra sessizce eziliyordu.
// Artik yazim aninda kopyalanir; kopyanin sahibi YUVA ADRESIDIR. Ayni yuvaya yeni yazimda (ya da
// rutin bitisinde __uxb_rt_str_release) yalniz o yuvanin kendi kopyasi serbest birakilir -- baska
// bir degiskenin metnine (b = a; parametre) hic dokunulmaz. Kayit defteri kilitli: gorevler guvenli.
std::mutex owned_text_mutex;
std::unordered_map<const char*, void*>& owned_texts() {
    static auto* table = new std::unordered_map<const char*, void*>();   // bilerek yok edilmez (S-030)
    return *table;
}

std::string text_or_empty(const char* value) {
    return value ? std::string(value) : std::string();
}

int64_t checked_count(int64_t value) {
    return value < 0 ? 0 : value;
}

// S-019: native LIST/DICT/SET storage. A handle is (slot index + 1); 0 is
// never a valid handle. Collections are never freed individually (matches the
// language's own LIST_NEW/DICT_NEW/SET_NEW surface, which has no FREE/DISPOSE
// call at all) -- they live for the process, same as native array/file state
// elsewhere in this runtime. Values crossing the C ABI are tagged
// (kind, packed 64-bit payload): kind 1=I64 (payload is the integer itself),
// 2=F64 (payload is the double's raw bit pattern via memcpy, not a cast),
// 3=STRING (payload is a `const char*` reinterpreted as int64_t; on input the
// callee copies it into its own std::string immediately, on output it is a
// pointer into the existing thread-local `hold_text` ring, same lifetime rule
// as every other string-returning __uxb_rt_* function in this file).
struct UxbCollValue {
    int64_t kind = 0;
    int64_t i64v = 0;
    double f64v = 0.0;
    std::string strv;
};

struct UxbCollection {
    std::string kind;                 // "LIST" / "DICT" / "SET"
    std::vector<UxbCollValue> values; // LIST: items in order. DICT: values, parallel to keys. SET: unused.
    std::vector<std::string> keys;    // DICT: key text, parallel to values. SET: member text. LIST: unused.
};

std::mutex collections_mutex;
std::vector<std::unique_ptr<UxbCollection>> collections;

// Caller must hold collections_mutex. Returns null on an invalid/out-of-range
// handle or a handle/expectedKind kind mismatch -- both are ordinary,
// expected failure modes here (not a fatal condition), so callers translate a
// null return into a plain 0/-1 status return, never an abort/exit.
UxbCollection* collection_at(int64_t handle, const char* expectedKind) {
    if (handle <= 0) return nullptr;
    const std::size_t idx = static_cast<std::size_t>(handle - 1);
    if (idx >= collections.size()) return nullptr;
    UxbCollection* c = collections[idx].get();
    if (expectedKind && c->kind != expectedKind) return nullptr;
    return c;
}

int64_t collection_new(const char* kindTag) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    collections.push_back(std::make_unique<UxbCollection>());
    collections.back()->kind = kindTag;
    return static_cast<int64_t>(collections.size());
}

void collection_value_from_packed(UxbCollValue& v, int64_t kind, int64_t packedValue) {
    v.kind = kind;
    if (kind == 1) {
        v.i64v = packedValue;
    } else if (kind == 2) {
        std::memcpy(&v.f64v, &packedValue, sizeof(double));
    } else if (kind == 3) {
        v.strv = text_or_empty(reinterpret_cast<const char*>(packedValue));
    }
}

int64_t collection_value_to_packed_out(const UxbCollValue& v, int64_t* out_value) {
    switch (v.kind) {
    case 1:
        if (out_value) *out_value = v.i64v;
        return 1;
    case 2:
        if (out_value) std::memcpy(out_value, &v.f64v, sizeof(double));
        return 2;
    case 3:
        if (out_value) *out_value = reinterpret_cast<int64_t>(hold_text(v.strv));
        return 3;
    default:
        return 0;
    }
}

std::FILE* channel_file(int64_t channel) {
    const auto it = files.find(channel);
    return it == files.end() ? nullptr : it->second;
}

int64_t host_task_call(const std::string& name, int64_t slot, int64_t input) {
    int output = 0;
    int rc = UXB_RT_FAILURE;
    if (name == "THREAD") rc = uxb_thread_start(static_cast<int>(slot), static_cast<int>(input), &output);
    else if (name == "PIPE") rc = uxb_pipe_run(static_cast<int>(slot), static_cast<int>(input), &output);
    else if (name == "PARALEL" || name == "PARALLEL") rc = uxb_parallel_run(static_cast<int>(slot), static_cast<int>(input), &output);
    else if (name == "TRIGGER" || name == "EVENT") rc = uxb_task_trigger(static_cast<int>(slot), static_cast<int>(input), &output);
    else if (name == "ON") rc = uxb_slot_on(static_cast<int>(slot));
    else if (name == "OFF") rc = uxb_slot_off(static_cast<int>(slot));
    else if (name == "SLOT") rc = uxb_slot_bind(static_cast<int>(slot), static_cast<int>(input), "MIR_SLOT");
    else {
        uxb::RuntimeState::instance().set_error("MIR host call is not bound: " + name);
        std::fprintf(stderr, "uXBasic runtime error: MIR host call is not bound: %s\n", name.c_str());
        return -1;
    }
    return rc == UXB_RT_SUCCESS ? static_cast<int64_t>(output) : -1;
}

// S-142b: the language's floating-point text rule, identical on every engine
// (src/common/float_text.fbs is the FreeBASIC-side twin): as many significant
// digits as the type carries (F64: 16, F32: 7), no padding zeros ("%g" trims
// them), exponent always at least two digits, "inf" / "-inf" / "nan", and
// negative zero reads "0".
std::string format_float_text(double value, int significant_digits) {
    if (value == 0.0) return "0";
    if (std::isnan(value)) return "nan";
    if (std::isinf(value)) return value < 0 ? "-inf" : "inf";
    char buf[64];
    std::snprintf(buf, sizeof(buf), "%.*g", significant_digits, value);
    std::string text(buf);
    const std::size_t exp_pos = text.find('e');
    if (exp_pos != std::string::npos && exp_pos + 2 < text.size()) {
        // Some Windows C runtimes write three exponent digits ("1e+020").
        std::size_t digits_at = exp_pos + 2;
        while (text.size() - digits_at > 2 && text[digits_at] == '0') text.erase(digits_at, 1);
    }
    return text;
}

std::string format_f64_text(double value) { return format_float_text(value, 16); }

std::string format_f32_text(double value) {
    return format_float_text(static_cast<double>(static_cast<float>(value)), 7);
}

}  // namespace

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_str_store(const char** slot, const char* src) {
    if (!slot) return 0;
    const char* old = *slot;
    if (src && src == old) return 0;
    const std::size_t n = src ? std::strlen(src) : 0;
    char* copy = static_cast<char*>(std::malloc(n + 1));
    if (!copy) return 0;
    if (n) std::memcpy(copy, src, n);
    copy[n] = '\0';
    {
        std::lock_guard<std::mutex> lock(owned_text_mutex);
        auto& table = owned_texts();
        if (old) {
            auto it = table.find(old);
            if (it != table.end() && it->second == static_cast<void*>(slot)) {
                std::free(const_cast<char*>(old));
                table.erase(it);
            }
        }
        table[copy] = static_cast<void*>(slot);
    }
    *slot = copy;
    return 1;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_str_release(const char** slot) {
    if (!slot || !*slot) return 0;
    std::lock_guard<std::mutex> lock(owned_text_mutex);
    auto& table = owned_texts();
    auto it = table.find(*slot);
    if (it == table.end() || it->second != static_cast<void*>(slot)) return 0;
    std::free(const_cast<char*>(*slot));
    table.erase(it);
    *slot = nullptr;
    return 1;
}

// Rutin donusu: yerel yuvanin kopyasi serbest birakilmadan once metin gecici halkaya alinir.
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_temp(const char* value) { return hold_text(text_or_empty(value)); }

// S-030 Faz 2A / K9: konsol ciktisinin tek yolu (bkz. uxb_runtime_print.h).
namespace {
std::mutex console_mutex;
thread_local std::string console_line;
}  // namespace

namespace uxb {

void console_write(const std::string& text) {
    if (!task_pool_active() && console_line.empty()) {
        std::fputs(text.c_str(), stdout);
        std::fflush(stdout);
        return;
    }
    console_line += text;
    const std::size_t lastNewline = console_line.rfind('\n');
    if (lastNewline == std::string::npos) return;
    {
        std::lock_guard<std::mutex> lock(console_mutex);
        std::fwrite(console_line.data(), 1, lastNewline + 1, stdout);
        std::fflush(stdout);
    }
    console_line.erase(0, lastNewline + 1);
}

void console_flush_current_thread() {
    if (console_line.empty()) return;
    std::lock_guard<std::mutex> lock(console_mutex);
    std::fwrite(console_line.data(), 1, console_line.size(), stdout);
    std::fflush(stdout);
    console_line.clear();
}

}  // namespace uxb

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_i64(int64_t value) {
    uxb::console_write(std::to_string(static_cast<long long>(value)));
    return value;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_cstr(const char* value) {
    const char* text = value ? value : "";
    uxb::console_write(text);
    return static_cast<int64_t>(std::strlen(text));
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_newline(void) {
    uxb::console_write("\n");
    return 1;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_f64(double value) {
    // S-142b: same digits rule as the interpreters (see format_float_text).
    uxb::console_write(format_f64_text(value));
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_print_f32(double value) {
    uxb::console_write(format_f32_text(value));
    return 0;
}

UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_f32(double value) {
    return hold_text(format_f32_text(value));
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_input_i64(void) {
    uxb::console_flush_current_thread();   // yarim satir istem (PRINT "Sayi: ";) girdiden once gorunmeli
    int64_t value = 0;
    if (!(std::cin >> value)) {
        uxb::RuntimeState::instance().set_error("INPUT expected an integer value");
        std::cin.clear();
        return 0;
    }
    return value;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_cls(void) {
    uxb::console_flush_current_thread();
#if defined(_WIN32)
    HANDLE out = GetStdHandle(STD_OUTPUT_HANDLE);
    CONSOLE_SCREEN_BUFFER_INFO info{};
    DWORD written = 0;
    if (out == INVALID_HANDLE_VALUE || !GetConsoleScreenBufferInfo(out, &info)) return 0;
    const DWORD cells = static_cast<DWORD>(info.dwSize.X) * static_cast<DWORD>(info.dwSize.Y);
    const COORD home{0, 0};
    if (!FillConsoleOutputCharacterA(out, ' ', cells, home, &written)) return 0;
    if (!FillConsoleOutputAttribute(out, info.wAttributes, cells, home, &written)) return 0;
    return SetConsoleCursorPosition(out, home) ? 1 : 0;
#else
    std::fputs("\033[2J\033[H", stdout);
    return 1;
#endif
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_locate(int64_t row, int64_t column) {
    uxb::console_flush_current_thread();
#if defined(_WIN32)
    COORD position{static_cast<SHORT>(std::max<int64_t>(1, column) - 1), static_cast<SHORT>(std::max<int64_t>(1, row) - 1)};
    return SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), position) ? 1 : 0;
#else
    std::printf("\033[%lld;%lldH", static_cast<long long>(row), static_cast<long long>(column));
    return 1;
#endif
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_color(int64_t foreground, int64_t background) {
    uxb::console_flush_current_thread();
#if defined(_WIN32)
    const WORD attributes = static_cast<WORD>((foreground & 15) | ((background & 15) << 4));
    return SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), attributes) ? 1 : 0;
#else
    std::printf("\033[%lld;%lldm", 30LL + (foreground & 7), 40LL + (background & 7));
    return 1;
#endif
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_getkey_i64(void) {
    uxb::console_flush_current_thread();
#if defined(_WIN32)
    return static_cast<unsigned char>(_getch());
#else
    return std::getchar();
#endif
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_inkey_i64(void) {
    uxb::console_flush_current_thread();
#if defined(_WIN32)
    return _kbhit() ? static_cast<unsigned char>(_getch()) : 0;
#else
    return 0;
#endif
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_timer_i64(void) {
    const std::time_t now = std::time(nullptr);
    std::tm local{};
#if defined(_WIN32)
    localtime_s(&local, &now);
#else
    localtime_r(&now, &local);
#endif
    return local.tm_hour * 3600LL + local.tm_min * 60LL + local.tm_sec;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_rnd_i64(void) {
    std::lock_guard<std::mutex> lock(random_mutex);
    return static_cast<int64_t>(random_engine() & 0x7fffffffffffffffULL);
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_randomize(int64_t seed) {
    std::lock_guard<std::mutex> lock(random_mutex);
    random_engine.seed(static_cast<uint64_t>(seed));
    return seed;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_strlen(const char* value) { return static_cast<int64_t>(text_or_empty(value).size()); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_val_i64(const char* value) {
    if (!value) return 0;
    char* end = nullptr;
    const long long result = std::strtoll(value, &end, 0);
    return end == value ? 0 : static_cast<int64_t>(result);
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_i64(int64_t value) { return hold_text(std::to_string(value)); }
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_u64(int64_t value) { return hold_text(std::to_string(static_cast<uint64_t>(value))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_asc(const char* value) { return value && *value ? static_cast<unsigned char>(*value) : 0; }
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_chr(int64_t value) { return hold_text(std::string(1, static_cast<char>(value & 255))); }
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_left(const char* value, int64_t count) {
    const std::string text = text_or_empty(value);
    return hold_text(text.substr(0, static_cast<std::size_t>(std::min<int64_t>(checked_count(count), text.size()))));
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_right(const char* value, int64_t count) {
    const std::string text = text_or_empty(value);
    const std::size_t length = static_cast<std::size_t>(std::min<int64_t>(checked_count(count), text.size()));
    return hold_text(text.substr(text.size() - length));
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_mid(const char* value, int64_t start, int64_t count) {
    const std::string text = text_or_empty(value);
    const std::size_t offset = static_cast<std::size_t>(std::max<int64_t>(1, start) - 1);
    if (offset >= text.size()) return hold_text("");
    if (count < 0) return hold_text(text.substr(offset));
    return hold_text(text.substr(offset, static_cast<std::size_t>(count)));
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_instr(const char* value, const char* needle, int64_t start) {
    const std::string text = text_or_empty(value);
    const std::string wanted = text_or_empty(needle);
    const std::size_t offset = static_cast<std::size_t>(std::max<int64_t>(1, start) - 1);
    const std::size_t found = text.find(wanted, offset);
    return found == std::string::npos ? 0 : static_cast<int64_t>(found + 1);
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_lcase(const char* value) {
    std::string text = text_or_empty(value);
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return hold_text(std::move(text));
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_ucase(const char* value) {
    std::string text = text_or_empty(value);
    std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return hold_text(std::move(text));
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_ltrim(const char* value) {
    std::string text = text_or_empty(value);
    text.erase(text.begin(), std::find_if(text.begin(), text.end(), [](unsigned char c) { return !std::isspace(c); }));
    return hold_text(std::move(text));
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_rtrim(const char* value) {
    std::string text = text_or_empty(value);
    text.erase(std::find_if(text.rbegin(), text.rend(), [](unsigned char c) { return !std::isspace(c); }).base(), text.end());
    return hold_text(std::move(text));
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_trim(const char* value) { return __uxb_rt_ltrim(__uxb_rt_rtrim(value)); }
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_space(int64_t count) { return hold_text(std::string(static_cast<std::size_t>(checked_count(count)), ' ')); }
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_hex(int64_t value) { std::ostringstream out; out << std::uppercase << std::hex << value; return hold_text(out.str()); }
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_oct(int64_t value) { std::ostringstream out; out << std::oct << value; return hold_text(out.str()); }
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_bin(int64_t value) {
    uint64_t bits = static_cast<uint64_t>(value);
    if (bits == 0) return hold_text("0");
    std::string out;
    while (bits) { out.push_back((bits & 1) ? '1' : '0'); bits >>= 1; }
    std::reverse(out.begin(), out.end());
    return hold_text(std::move(out));
}
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_concat(const char* left, const char* right) { return hold_text(text_or_empty(left) + text_or_empty(right)); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_str_compare(const char* left, const char* right) {
    const int result = text_or_empty(left).compare(text_or_empty(right));
    return result < 0 ? -1 : (result > 0 ? 1 : 0);
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_memcopy(void* dst, const void* src, int64_t bytes) {
    if (!dst || !src || bytes < 0) return 0;
    std::memmove(dst, src, static_cast<std::size_t>(bytes));
    return bytes;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_memfill(void* dst, int64_t value, int64_t bytes) {
    if (!dst || bytes < 0) return 0;
    std::memset(dst, static_cast<unsigned char>(value), static_cast<std::size_t>(bytes));
    return bytes;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_peek_i64(const int64_t* address) { return address ? *address : 0; }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_poke_i64(int64_t* address, int64_t value) { if (!address) return 0; *address = value; return value; }
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_mem_read_sequence(const void* address, int64_t length) {
    if (!address || length < 0) return nullptr;
    const auto* bytes = static_cast<const unsigned char*>(address);
    return hold_text(std::string(reinterpret_cast<const char*>(bytes), static_cast<std::size_t>(length)));
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_mem_write_sequence(void* address, const char* source, int64_t length) {
    if (!address || !source || length < 0) return 0;
    std::memcpy(address, source, static_cast<std::size_t>(length));
    return length;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_open(const char* path, const char* mode, int64_t channel, int64_t) {
    if (!path || !mode || channel < 0) return 0;
    std::lock_guard<std::mutex> lock(file_mutex);
    if (std::FILE* old = channel_file(channel)) std::fclose(old);
    // S-146 adim 2: BASIC kip sozcukleri C fopen kiplerine cevrilir (onceden "OUTPUT" dogrudan fopen'a
    // gidiyor, dosya hic acilmiyordu). C kipi ("w", "rb" ...) verilmisse oldugu gibi kullanilir.
    const std::string m = text_or_empty(mode);
    std::string mu;
    for (char c : m) mu.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
    std::FILE* file = nullptr;
    if (mu == "OUTPUT" || mu == "O") file = std::fopen(path, "w");
    else if (mu == "INPUT" || mu == "I" || mu == "IN") file = std::fopen(path, "r");
    else if (mu == "APPEND" || mu == "A") file = std::fopen(path, "a");
    else if (mu == "BINARY" || mu == "B" || mu == "RANDOM" || mu == "R") {
        file = std::fopen(path, "r+b");
        if (!file) file = std::fopen(path, "w+b");
    } else {
        file = std::fopen(path, mode);
    }
    if (!file) { files.erase(channel); return 0; }
    files[channel] = file;
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_close(int64_t channel) {
    std::lock_guard<std::mutex> lock(file_mutex);
    std::FILE* file = channel_file(channel);
    if (!file) return 0;
    const int result = std::fclose(file);
    files.erase(channel);
    return result == 0 ? 1 : 0;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_seek(int64_t channel, int64_t position) {
    std::lock_guard<std::mutex> lock(file_mutex);
    std::FILE* file = channel_file(channel);
    if (!file) return -1;
    if (position >= 0 && std::fseek(file, static_cast<long>(position), SEEK_SET) != 0) return -1;
    return static_cast<int64_t>(std::ftell(file));
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_eof(int64_t channel) {
    std::lock_guard<std::mutex> lock(file_mutex);
    std::FILE* file = channel_file(channel);
    if (!file) return 1;
    const int ch = std::fgetc(file);
    if (ch == EOF) return 1;
    std::ungetc(ch, file);
    return 0;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_lof(int64_t channel) {
    std::lock_guard<std::mutex> lock(file_mutex);
    std::FILE* file = channel_file(channel);
    if (!file) return -1;
    const long current = std::ftell(file);
    if (std::fseek(file, 0, SEEK_END) != 0) return -1;
    const long length = std::ftell(file);
    std::fseek(file, current, SEEK_SET);
    return static_cast<int64_t>(length);
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_get(int64_t channel, int64_t position, int64_t bytes) {
    std::lock_guard<std::mutex> lock(file_mutex);
    std::FILE* file = channel_file(channel);
    if (!file) return -1;
    if (position >= 0 && std::fseek(file, static_cast<long>(position), SEEK_SET) != 0) return -1;
    if (bytes <= 1) return std::fgetc(file);
    int64_t value = 0;
    const std::size_t count = static_cast<std::size_t>(std::min<int64_t>(bytes, sizeof(value)));
    return std::fread(&value, 1, count, file) == count ? value : -1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_put(int64_t channel, int64_t position, int64_t bytes, int64_t value) {
    std::lock_guard<std::mutex> lock(file_mutex);
    std::FILE* file = channel_file(channel);
    if (!file) return 0;
    if (position >= 0 && std::fseek(file, static_cast<long>(position), SEEK_SET) != 0) return 0;
    const std::size_t count = static_cast<std::size_t>(std::max<int64_t>(1, std::min<int64_t>(bytes, sizeof(value))));
    return std::fwrite(&value, 1, count, file) == count ? static_cast<int64_t>(count) : 0;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_delete(const char* path) { return path && std::remove(path) == 0 ? 1 : 0; }
// S-146 adim 2: metin dosyasi PRINT # / INPUT # (yorumlayicilarla ayni bicim). Satir, is parcacigina
// ozel tamponda birlesir ve dosyaya TEK kilit altinda yazilir: gorevlerin satirlari karismaz.
// Ayrac: ";" hicbir sey, "," sekme, " " bosluk; son ayrac ";" ya da "," degilse satir sonu yazilir.
namespace {
thread_local std::string tl_filePrintBuffer;
thread_local int64_t tl_filePrintChannel = -1;
thread_local std::string tl_filePrintLastSep;
}  // namespace

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_print_begin(int64_t channel) {
    tl_filePrintBuffer.clear();
    tl_filePrintChannel = channel;
    tl_filePrintLastSep.clear();
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_print_text(const char* text, const char* sep) {
    tl_filePrintBuffer += text_or_empty(text);
    tl_filePrintLastSep = text_or_empty(sep);
    if (tl_filePrintLastSep == ",") tl_filePrintBuffer += '\t';
    else if (tl_filePrintLastSep == " ") tl_filePrintBuffer += ' ';
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_file_print_end(void) {
    const bool raw = (tl_filePrintLastSep == ";" || tl_filePrintLastSep == ",");
    std::lock_guard<std::mutex> lock(file_mutex);
    std::FILE* file = channel_file(tl_filePrintChannel);
    tl_filePrintChannel = -1;
    if (!file) return 0;
    if (!tl_filePrintBuffer.empty()) std::fwrite(tl_filePrintBuffer.data(), 1, tl_filePrintBuffer.size(), file);
    if (!raw) std::fputc('\n', file);
    tl_filePrintBuffer.clear();
    return 1;
}

// INPUT #: bir satir (satir sonu olmadan); dosya sonunda bos metin.
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_file_input_line(int64_t channel) {
    std::string line;
    {
        std::lock_guard<std::mutex> lock(file_mutex);
        std::FILE* file = channel_file(channel);
        if (file) {
            int ch;
            while ((ch = std::fgetc(file)) != EOF) {
                if (ch == '\n') break;
                if (ch != '\r') line.push_back(static_cast<char>(ch));
            }
        }
    }
    return hold_text(line);
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_sqrt_i64(int64_t value) { return value < 0 ? 0 : static_cast<int64_t>(std::sqrt(static_cast<double>(value))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_sin_i64(int64_t value) { return static_cast<int64_t>(std::sin(static_cast<double>(value))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_cos_i64(int64_t value) { return static_cast<int64_t>(std::cos(static_cast<double>(value))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_tan_i64(int64_t value) { return static_cast<int64_t>(std::tan(static_cast<double>(value))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_atn_i64(int64_t value) { return static_cast<int64_t>(std::atan(static_cast<double>(value))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_log_i64(int64_t value) { return value <= 0 ? 0 : static_cast<int64_t>(std::log(static_cast<double>(value))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exp_i64(int64_t value) { return static_cast<int64_t>(std::exp(static_cast<double>(value))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_pow_i64(int64_t left, int64_t right) { return static_cast<int64_t>(std::pow(static_cast<double>(left), static_cast<double>(right))); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_assert_i64(int64_t condition) {
    if (condition) return condition;
    std::fputs("uXBasic ASSERT failed\n", stderr);
    std::fflush(stderr);
    std::abort();
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_host_call(const char* name) { return __uxb_rt_host_call4(name, 0, 0, 0); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_host_call4(const char* name, int64_t a, int64_t b, int64_t) {
    std::string normalized = text_or_empty(name);
    std::transform(normalized.begin(), normalized.end(), normalized.begin(), [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return host_task_call(normalized, a, b);
}

// S-019 native LIST/DICT/SET C ABI. Every function here is a pure library
// call: it never prints, never exits, never aborts -- on failure (invalid
// handle, wrong-kind handle, out-of-range index, missing key) it returns a
// plain 0/-1 status and leaves the collection untouched. The emitted x64 code
// is responsible for checking that status and, on failure, calling
// __uxb_rt_runtime_error_exit itself with a message naming the failed
// operation -- this keeps "how a runtime error is reported" a single,
// generic, compiler-owned concern instead of duplicating print+exit logic
// inside every collection accessor.
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_new(void) { return collection_new("LIST"); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_new(void) { return collection_new("DICT"); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_new(void) { return collection_new("SET"); }

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_len(int64_t handle) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "LIST");
    return c ? static_cast<int64_t>(c->values.size()) : -1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_len(int64_t handle) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "DICT");
    return c ? static_cast<int64_t>(c->keys.size()) : -1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_len(int64_t handle) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "SET");
    return c ? static_cast<int64_t>(c->keys.size()) : -1;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_get(int64_t handle, int64_t index, int64_t* out_value) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "LIST");
    if (!c || index < 0 || static_cast<std::size_t>(index) >= c->values.size()) return 0;
    return collection_value_to_packed_out(c->values[static_cast<std::size_t>(index)], out_value);
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_set(int64_t handle, int64_t index, int64_t kind, int64_t packed_value) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "LIST");
    if (!c || index < 0 || static_cast<std::size_t>(index) >= c->values.size() || kind < 1 || kind > 3) return 0;
    collection_value_from_packed(c->values[static_cast<std::size_t>(index)], kind, packed_value);
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_add(int64_t handle, int64_t kind, int64_t packed_value) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "LIST");
    if (!c || kind < 1 || kind > 3) return 0;
    UxbCollValue v;
    collection_value_from_packed(v, kind, packed_value);
    c->values.push_back(std::move(v));
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_remove(int64_t handle, int64_t index) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "LIST");
    if (!c || index < 0 || static_cast<std::size_t>(index) >= c->values.size()) return 0;
    c->values.erase(c->values.begin() + static_cast<std::ptrdiff_t>(index));
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_list_clear(int64_t handle) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "LIST");
    if (!c) return 0;
    c->values.clear();
    return 1;
}

namespace {
// -1 when not found. Caller must hold collections_mutex.
std::ptrdiff_t collection_key_index(const UxbCollection& c, const std::string& key) {
    for (std::size_t i = 0; i < c.keys.size(); ++i) {
        if (c.keys[i] == key) return static_cast<std::ptrdiff_t>(i);
    }
    return -1;
}
}  // namespace

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_has(int64_t handle, const char* key) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "DICT");
    if (!c) return 0;
    // -1, not 1: matches the interpreters' own BOOL(true) representation
    // (FreeBASIC's native boolean TRUE is -1, all bits set), which is what a
    // BASIC program actually observes from e.g. CINT(DICTHAS(...)).
    return collection_key_index(*c, text_or_empty(key)) >= 0 ? -1 : 0;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_get(int64_t handle, const char* key, int64_t* out_value) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "DICT");
    if (!c) return 0;
    const std::ptrdiff_t idx = collection_key_index(*c, text_or_empty(key));
    if (idx < 0) return 0;
    return collection_value_to_packed_out(c->values[static_cast<std::size_t>(idx)], out_value);
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_set(int64_t handle, const char* key, int64_t kind, int64_t packed_value) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "DICT");
    if (!c || kind < 1 || kind > 3) return 0;
    const std::string keyText = text_or_empty(key);
    const std::ptrdiff_t idx = collection_key_index(*c, keyText);
    if (idx >= 0) {
        // DICTSET on an existing key overwrites in place -- it does not move
        // the key to the end of insertion order (matches
        // mir_interp_collections.fbs's DICTSET exactly).
        collection_value_from_packed(c->values[static_cast<std::size_t>(idx)], kind, packed_value);
        return 1;
    }
    UxbCollValue v;
    collection_value_from_packed(v, kind, packed_value);
    c->keys.push_back(keyText);
    c->values.push_back(std::move(v));
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_clear(int64_t handle) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "DICT");
    if (!c) return 0;
    c->keys.clear();
    c->values.clear();
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_key_at(int64_t handle, int64_t index, const char** out_key) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "DICT");
    if (!c || index < 0 || static_cast<std::size_t>(index) >= c->keys.size()) return 0;
    if (out_key) *out_key = hold_text(c->keys[static_cast<std::size_t>(index)]);
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_dict_value_at(int64_t handle, int64_t index, int64_t* out_value) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "DICT");
    if (!c || index < 0 || static_cast<std::size_t>(index) >= c->values.size()) return 0;
    return collection_value_to_packed_out(c->values[static_cast<std::size_t>(index)], out_value);
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_has(int64_t handle, const char* member) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "SET");
    if (!c) return 0;
    // -1, not 1: see __uxb_rt_dict_has's comment.
    return collection_key_index(*c, text_or_empty(member)) >= 0 ? -1 : 0;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_add(int64_t handle, const char* member) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "SET");
    if (!c) return 0;
    const std::string memberText = text_or_empty(member);
    if (collection_key_index(*c, memberText) < 0) c->keys.push_back(memberText);
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_remove(int64_t handle, const char* member) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "SET");
    if (!c) return 0;
    // Matches mir_interp_collections.fbs's SETREMOVE: removing an absent
    // member is a successful no-op, not an error.
    const std::ptrdiff_t idx = collection_key_index(*c, text_or_empty(member));
    if (idx >= 0) c->keys.erase(c->keys.begin() + idx);
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_clear(int64_t handle) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "SET");
    if (!c) return 0;
    c->keys.clear();
    return 1;
}
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_set_member_at(int64_t handle, int64_t index, const char** out_member) {
    std::lock_guard<std::mutex> lock(collections_mutex);
    UxbCollection* c = collection_at(handle, "SET");
    if (!c || index < 0 || static_cast<std::size_t>(index) >= c->keys.size()) return 0;
    if (out_member) *out_member = hold_text(c->keys[static_cast<std::size_t>(index)]);
    return 1;
}

// STR() / concatenation / DICT-SET key text of an F64 value: the language's
// floating text rule (format_float_text, S-142b), identical to what the
// interpreters print. S-047 (Codex) fixed a 6-digit "%g" here that made distinct
// keys such as 1.0000001 and 1.0000002 collide; 16 significant digits keep
// them apart and match the interpreters' own key text. Negative zero reads "0",
// so -0.0 and 0.0 can never be two different keys.
UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_str_f64(double value) {
    return hold_text(format_f64_text(value));
}

// Generic controlled-error exit for emitted x64 code: prints a message (the
// TR/EN diagnostic text the compiler already generates at the call site) and
// exits cleanly with a non-zero code. Deliberately NOT called by any of the
// collection accessors above -- only the emitter calls this, after it has
// already checked a 0/-1 status for itself. Uses std::exit (unwinds C++
// destructors, flushes streams), not std::abort (SIGABRT / no cleanup), since
// this is an ordinary, expected language-level runtime error, not a fatal
// internal-invariant violation.
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_runtime_error_exit(const char* message) {
    uxb::console_flush_current_thread();
    std::fputs(message ? message : "uXBasic runtime error", stderr);
    std::fputc('\n', stderr);
    std::fflush(stderr);
    std::exit(1);
}
