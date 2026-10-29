// S-030 Faz 2A — native gorev calisma zamani, ABI v2.
// Tasarim: docs/tasarim/UXB_S030_FAZ2A_NATIVE_ASYNC_PLANI_20260925_TR.md
// Mete kararlari: K4 (sinirli isci havuzu, AUTO = mantiksal CPU, --task-workers N,
// bekleyen isci kuyruktan is calistirir), K5 (normal kapanis gorevleri bekler;
// okunmamis gorev hatasi hata cikisina yazilir, cikis kodu basarisiz), K6
// (isbirlikci iptal; STATUS=CANCELLED, ERRORTEXT="CANCELLED"; JOIN/RESULT iptali
// cagirana aktarir; tekrar CANCEL zararsiz), K9 (PRINT ayri dosyada).
//
// Kod uretimi sozlesmesi (thunk): derleyici SPAWN hedefi olan her lane icin
//     int64_t thunk(void* block)
// uretir. block[0..7] sonuc yuvasidir (thunk yazar), block[8..] argumanlardir
// (her biri 8 bayt; tamsayi degeri, F64 bit deseni ya da STRING icin kopyalanmis
// metnin adresi). Thunk 0 doner; yakalanmamis THROW'u lane icinden
// __uxb_rt_task_fail_* ile bildirir. Deger turleri koleksiyonlarla ayni:
// 0=VOID, 1=I64, 2=F64, 3=STRING.

#include "uxb_runtime.h"
#include "uxb_runtime_print.h"
#include "uxb_runtime_text.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#if defined(_WIN32)
#include <process.h>
#include <windows.h>
#endif

namespace {

typedef int64_t (UXB_RT_CDECL *uxb_task_thunk_v2)(void* block);

// S-163 / S-146 madde 9: RND/RANDOMIZE -- AST/MIR yorumlayicilariyla (src/common/uxb_rng.fbs) BIREBIR
// ayni uretec: xoshiro256**, durum SplitMix64 ile tohumlanir. Her gorev SPAWN aninda ata uretecinin
// siradaki 64 bitlik degeriyle tohumlanir (belirlenimci, motorlar arasi ayni dizi).
struct UxbRng {
    uint64_t s[4] = {0, 0, 0, 0};
    double lastValue = 0.0;
    static uint64_t splitmix(uint64_t& x) {
        x += 0x9E3779B97F4A7C15ULL;
        uint64_t z = x;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
        return z ^ (z >> 31);
    }
    static uint64_t rotl(uint64_t v, int k) { return (v << k) | (v >> (64 - k)); }
    void seed(uint64_t seedValue) {
        uint64_t x = seedValue;
        s[0] = splitmix(x);
        s[1] = splitmix(x);
        s[2] = splitmix(x);
        s[3] = splitmix(x);
        lastValue = 0.0;
    }
    uint64_t next() {
        const uint64_t result = rotl(s[1] * 5ULL, 7) * 9ULL;
        const uint64_t t = s[1] << 17;
        s[2] ^= s[0];
        s[3] ^= s[1];
        s[1] ^= s[2];
        s[0] ^= s[3];
        s[2] ^= t;
        s[3] = rotl(s[3], 45);
        return result;
    }
    double nextF64() {
        lastValue = static_cast<double>(next() >> 11) * (1.0 / 9007199254740992.0);
        return lastValue;
    }
};
const uint64_t kRngDefaultSeed = 0x5EED0000C0FFEE01ULL;

enum TaskStateV2 { TS_PENDING = 0, TS_RUNNING = 1, TS_DONE = 2, TS_ERROR = 3, TS_CANCELLED = 4 };
const int64_t kValueVoid = 0;
const int64_t kValueString = 3;

struct TaskRunV2 {
    int64_t id = 0;
    std::string name;
    int state = TS_PENDING;
    uxb_task_thunk_v2 thunk = nullptr;
    std::vector<unsigned char> block;
    int64_t resultKind = kValueVoid;
    int64_t resultBits = 0;
    std::string resultText;
    std::string errorText;
    bool errorObserved = false;
    std::atomic<bool> cancelRequested{false};
    std::vector<std::string> argTexts;   // STRING argumanlarinin gorev omrunce sahibi kopyalari
    UxbRng rng;                          // S-146 madde 9: gorevin kendi RND uretecu
};

// Ana programin uretecu (gorevler kendi kayitlarindakini kullanir). Ilk kullanimda varsayilan tohum.
UxbRng& main_rng() {
    static UxbRng* r = [] { auto* p = new UxbRng(); p->seed(kRngDefaultSeed); return p; }();
    return *r;
}

struct TaskGroupV2 {
    std::vector<int64_t> members;
};

// Paylasilan durum bilerek yigindan alinir ve HIC yok edilmez: ANSI exit() statik yikicilari
// calistirir; o sirada hala calisan isciler yok edilmis bir mutex'e dokunur ya da birlesmemis
// std::thread yikicisi std::terminate cagirir (olumcul JOIN hatasi = exit(1) yolu).
struct TaskRuntimeStateV2 {
    std::mutex mutex;
    std::condition_variable workAvailable;
    std::condition_variable taskFinished;
    std::deque<int64_t> queue;
    std::vector<std::unique_ptr<TaskRunV2>> tasks;     // id = indeks + 1
    std::vector<std::unique_ptr<TaskGroupV2>> groups;  // id = indeks + 1
#if defined(_WIN32)
    std::vector<HANDLE> workers;       // _beginthreadex: yigin boyutu acikca verilebilsin diye
#else
    std::vector<std::thread> workers;
#endif
    bool poolStarted = false;
    bool stopping = false;
    int workerCount = 0;       // yapilandirilan (K4) isci sayisi -- __uxb_rt_task_worker_count bunu raporlar
    int extraWorkers = 0;      // S-146: tum isciler beklerken kuyrukta is kaldiginda acilan telafi iscileri
    int idleWorkers = 0;       // kuyruk bekleyen isciler
    int blockedWorkers = 0;    // gorev/kilit bekleyen isciler
};
TaskRuntimeStateV2& S() {
    static TaskRuntimeStateV2* state = new TaskRuntimeStateV2();
    return *state;
}
#define g_mutex (S().mutex)
#define g_workAvailable (S().workAvailable)
#define g_taskFinished (S().taskFinished)
#define g_queue (S().queue)
#define g_tasks (S().tasks)
#define g_groups (S().groups)
#define g_workers (S().workers)
#define g_poolStarted (S().poolStarted)
#define g_stopping (S().stopping)
#define g_workerCount (S().workerCount)

thread_local TaskRunV2* tl_current = nullptr;
thread_local bool tl_isWorker = false;
// Calisan gorevin (yoksa ana programin) RND uretecu. Her uretece yalniz sahibi olan gorevin
// is parcacigi dokunur (gorev bir kerede tek is parcacigida calisir) -- kilit gerekmez.
UxbRng& current_rng() { return tl_current ? tl_current->rng : main_rng(); }
std::atomic<bool> g_poolActive{false};   // K9: konsol satir tamponu bu bayrakla devreye girer (kilitsiz okuma)

void start_worker_locked();

// STATUS/ERRORTEXT metin donusleri: cagiran is parcacigina ozel halka; ayni ifadede iki cagri
// (ornek: t.STATUS + t.ERRORTEXT) birbirini ezmez. uxb_runtime_mir.cpp hold_text ile ayni kural.
const char* hold_task_text(const std::string& value) {
    return uxb::hold_text_span(value);
}

const char* state_name(int s) {
    switch (s) {
    case TS_PENDING: return "PENDING";
    case TS_RUNNING: return "RUNNING";
    case TS_DONE: return "DONE";
    case TS_ERROR: return "ERROR";
    case TS_CANCELLED: return "CANCELLED";
    default: return "PENDING";
    }
}

bool is_finished(int s) { return s == TS_DONE || s == TS_ERROR || s == TS_CANCELLED; }

[[noreturn]] void runtime_fatal(const std::string& message) {
    uxb::console_flush_current_thread();
    std::fwrite(message.data(), 1, message.size(), stderr);
    std::fputc('\n', stderr);
    std::fflush(stderr);
    std::exit(1);
}

// Kilit tutulurken cagrilir.
TaskRunV2* task_at_locked(int64_t handle) {
    if (handle <= 0) return nullptr;
    const std::size_t idx = static_cast<std::size_t>(handle - 1);
    if (idx >= g_tasks.size()) return nullptr;
    return g_tasks[idx].get();
}

TaskGroupV2* group_at_locked(int64_t handle) {
    if (handle <= 0) return nullptr;
    const std::size_t idx = static_cast<std::size_t>(handle - 1);
    if (idx >= g_groups.size()) return nullptr;
    return g_groups[idx].get();
}

std::atomic<int> g_embeddedWorkers{0};   // --task-workers N (derleyici gomer); 0 = verilmedi

// Oncelik: UXB_TASK_WORKERS ortam degiskeni > derleyicinin gomdugu --task-workers > mantiksal CPU (K4).
int configured_worker_count() {
    const char* raw = std::getenv("UXB_TASK_WORKERS");
    if (raw && *raw) {
        const long v = std::strtol(raw, nullptr, 10);
        if (v >= 1 && v <= 1024) return static_cast<int>(v);
    }
    const int embedded = g_embeddedWorkers.load();
    if (embedded >= 1) return embedded;
    const unsigned hw = std::thread::hardware_concurrency();
    return hw == 0 ? 4 : static_cast<int>(hw);
}

// Gorevi calistirir. Kilit TUTULMADAN cagrilir.
void run_task(TaskRunV2* t) {
    {
        std::lock_guard<std::mutex> lock(g_mutex);
        if (t->cancelRequested.load()) {
            // K6: baslamamis gorev hic calismadan CANCELLED olur.
            t->state = TS_CANCELLED;
            t->errorText = "CANCELLED";
            g_taskFinished.notify_all();
            return;
        }
        t->state = TS_RUNNING;
    }
    TaskRunV2* previous = tl_current;
    tl_current = t;
    std::string failure;
    try {
        t->thunk(t->block.data());
    } catch (const std::exception& ex) {
        failure = std::string("native gorev ic hatasi: ") + ex.what();
    } catch (...) {
        failure = "native gorev ic hatasi";
    }
    // Flush under the task that owns the text and its explicit CONSOLE lock.
    // A nested run must not flush the suspended caller's unfinished line.
    uxb::console_finish_current_task();
    // S-146: gorev biterken (normal ya da hatayla) hala tuttugu kilitler birakilir.
    uxb::sync_release_all(t->id);
    // K9: gorevin yarim kalan satiri (PRINT x; ile biten) gorev bitiminde yazilir, baska gorevle karismaz.
    tl_current = previous;

    std::lock_guard<std::mutex> lock(g_mutex);
    if (!failure.empty() && t->errorText.empty()) t->errorText = failure;
    if (!t->errorText.empty() && t->state == TS_RUNNING) {
        t->state = (t->errorText == "CANCELLED") ? TS_CANCELLED : TS_ERROR;
    } else if (t->state == TS_RUNNING) {
        std::memcpy(&t->resultBits, t->block.data(), sizeof(int64_t));
        if (t->resultKind == kValueString) {
            // Lane sonucu isci is parcacigina ozel metin halkasinda; gorev kaydina kopyalanir.
            const char* p = nullptr;
            std::memcpy(&p, &t->resultBits, sizeof(p));
            t->resultText = uxb::copy_text(p);
        }
        t->state = TS_DONE;
    }
    g_taskFinished.notify_all();
}

void worker_main() {
    tl_isWorker = true;
    for (;;) {
        TaskRunV2* next = nullptr;
        {
            std::unique_lock<std::mutex> lock(g_mutex);
            S().idleWorkers++;
            g_workAvailable.wait(lock, [] { return g_stopping || !g_queue.empty(); });
            S().idleWorkers--;
            if (g_queue.empty()) {
                if (g_stopping) return;
                continue;
            }
            next = task_at_locked(g_queue.front());
            g_queue.pop_front();
        }
        if (next) run_task(next);
    }
}

#if defined(_WIN32)
unsigned __stdcall worker_entry_win32(void*) {
    worker_main();
    return 0;
}
#endif

void start_worker_locked() {
#if defined(_WIN32)
    // Isci yigini 8 MB: ana is parcaciginin (1 MB PE varsayilani) ve C++ varsayilaninin ustunde; gorev
    // govdesindeki derin ozyineleme ana programla ayni ya da daha genis alan bulur.
    const uintptr_t h = _beginthreadex(nullptr, 8u * 1024u * 1024u, &worker_entry_win32, nullptr, STACK_SIZE_PARAM_IS_A_RESERVATION, nullptr);
    if (h == 0) runtime_fatal("native: gorev iscisi baslatilamadi");
    g_workers.push_back(reinterpret_cast<HANDLE>(h));
#else
    g_workers.emplace_back(worker_main);
#endif
}

void ensure_pool_locked() {
    if (g_poolStarted) return;
    g_poolStarted = true;
    g_poolActive.store(true);
    g_workerCount = configured_worker_count();
    for (int i = 0; i < g_workerCount; ++i) start_worker_locked();
}

// S-146: kuyrukta is varken hic bos isci yok ve tum isciler bekliyorsa (kilit ya da gorev) ilerleme
// icin bir telafi iscisi acilir. Boylece kilit tutan bekleyici kuyruktaki isi kendi uzerinde
// calistirmasa da program ilerler.
void maybe_add_worker_locked() {
    if (!g_poolStarted || g_stopping || g_queue.empty()) return;
    if (S().idleWorkers > 0) return;
    if (S().blockedWorkers < g_workerCount + S().extraWorkers) return;
    S().extraWorkers++;
    start_worker_locked();
}

// K4: bekleyen is parcacigi, beklenen gorev bitene kadar kuyruktan is calistirir
// (ic ice SPAWN'da tum isciler birbirini bekleyip kilitlenmesin). S-146: bekleyici bir kilit
// tutuyorsa ya da sistemde acik LOCK varsa kendi uzerinde gorev calistirmaz (calistirdigi gorev
// o kilidi isteyip altta kalan bekleyiciyi kilitleyebilirdi); telafi iscisi ilerlemeyi saglar.
// Bekleme grafigine "ben -> beklenen gorev" kenari yazilir: cevrim LOCK_DEADLOCK tanisidir.
void wait_finished(int64_t handle) {
    const int64_t me = uxb::current_task_key();
    uxb::sync_note_wait_task(me, handle);
    for (;;) {
        const bool mayHelp = !uxb::sync_holds_any(me) && uxb::sync_explicit_total() == 0;
        TaskRunV2* toRun = nullptr;
        {
            std::unique_lock<std::mutex> lock(g_mutex);
            TaskRunV2* t = task_at_locked(handle);
            if (!t || is_finished(t->state)) break;
            if (mayHelp && !g_queue.empty()) {
                toRun = task_at_locked(g_queue.front());
                g_queue.pop_front();
            } else {
                if (tl_isWorker) S().blockedWorkers++;
                maybe_add_worker_locked();
                g_taskFinished.wait(lock);
                if (tl_isWorker) S().blockedWorkers--;
                continue;
            }
        }
        if (toRun) {
            uxb::sync_note_wait_task(me, toRun->id);
            run_task(toRun);
            uxb::sync_note_wait_task(me, handle);
        }
    }
    uxb::sync_clear_wait(me);
}

std::string failure_message_locked(TaskRunV2* t) {
    if (t->state == TS_CANCELLED) return "gorev iptal edildi (" + t->name + "): CANCELLED";
    return "gorev hatasi (" + t->name + "): " + t->errorText;
}

int64_t result_value_locked(TaskRunV2* t) {
    if (t->resultKind == kValueString) {
        const char* p = uxb::hold_text_span(t->resultText);
        int64_t bits = 0;
        std::memcpy(&bits, &p, sizeof(p));
        return bits;
    }
    return t->resultBits;
}

}  // namespace

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_spawn(void* thunk, const void* argblock, int64_t bytes, const char* name, int64_t resultKind, int64_t stringArgMask) {
    if (!thunk) runtime_fatal("native: SPAWN: gorev giris noktasi yok");
    if (bytes < 8) bytes = 8;
    auto t = std::make_unique<TaskRunV2>();
    t->name = name ? name : "";
    t->thunk = reinterpret_cast<uxb_task_thunk_v2>(thunk);
    t->resultKind = resultKind;
    t->block.assign(static_cast<std::size_t>(bytes), 0);
    if (argblock) std::memcpy(t->block.data(), argblock, static_cast<std::size_t>(bytes));
    // STRING argumanlari (bit i => block[8 + 8*i]) cagiranin gecici metnine isaret eder;
    // gorev baslamadan once kaydin sahip oldugu kopyaya yonlendirilir.
    const int64_t argSlots = (bytes - 8) / 8;
    for (int64_t i = 0; i < argSlots && i < 62; ++i) {
        if ((stringArgMask >> i) & 1) {
            const char* p = nullptr;
            std::memcpy(&p, t->block.data() + 8 + 8 * i, sizeof(p));
            t->argTexts.emplace_back(uxb::copy_text(p));
        } else {
            t->argTexts.emplace_back();
        }
    }
    for (int64_t i = 0; i < argSlots && i < 62; ++i) {
        if ((stringArgMask >> i) & 1) {
            const char* owned = t->argTexts[static_cast<std::size_t>(i)].c_str();
            // The task table retains these immutable argument strings for
            // process lifetime. Workers must see the same byte length.
            uxb::register_persistent_text(owned, t->argTexts[static_cast<std::size_t>(i)].size());
            std::memcpy(t->block.data() + 8 + 8 * i, &owned, sizeof(owned));
        }
    }
    t->rng.seed(current_rng().next());   // S-146 madde 9: ata baglaminda, SPAWN aninda
    std::lock_guard<std::mutex> lock(g_mutex);
    ensure_pool_locked();
    t->id = static_cast<int64_t>(g_tasks.size()) + 1;
    const int64_t id = t->id;
    g_tasks.push_back(std::move(t));
    g_queue.push_back(id);
    g_workAvailable.notify_one();
    maybe_add_worker_locked();
    return id;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_fail_cstr(const char* message) {
    if (!tl_current) runtime_fatal(std::string("uncaught THROW ") + uxb::copy_text(message));
    std::lock_guard<std::mutex> lock(g_mutex);
    if (tl_current->errorText.empty()) tl_current->errorText = std::string("native: uncaught THROW ") + uxb::copy_text(message);
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_fail_i64(int64_t value) {
    return __uxb_rt_task_fail_cstr(std::to_string(value).c_str());
}

// S-160: THROW/ASSERT istisna durumu is parcacigina (dolayisiyla calisan goreve) ozeldir; rutin
// sinirini gecer (kod uretimi her kullanici cagrisindan sonra __uxb_rt_exc_active'i denetler).
namespace {
thread_local int64_t tl_excActive = 0;
thread_local int64_t tl_excBits = 0;
thread_local bool tl_excIsString = false;
thread_local std::string tl_excText;
}  // namespace

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exc_active(void) { return tl_excActive; }

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exc_set_active(int64_t value) {
    tl_excActive = value ? 1 : 0;
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exc_set_value(int64_t bits, int64_t isString) {
    tl_excIsString = (isString != 0);
    if (tl_excIsString) {
        const char* p = nullptr;
        std::memcpy(&p, &bits, sizeof(p));
        tl_excText = uxb::copy_text(p);   // preserve bytes from the throwing frame
        tl_excBits = 0;
    } else {
        tl_excText.clear();
        tl_excBits = bits;
    }
    return 0;
}

// MAIN ya da gorev lane'i donerken: istisna hala aciksa yakalanmamistir. Ana programda deger
// eskisi gibi yazilir; gorevde gorev kaydina ERROR olarak gecer. 1 = yakalanmamis istisna vardi.
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_exc_uncaught(int64_t inTask) {
    if (!tl_excActive) return 0;
    const std::string text = tl_excIsString ? tl_excText : std::to_string(tl_excBits);
    tl_excActive = 0;
    tl_excBits = 0;
    tl_excIsString = false;
    tl_excText.clear();
    if (inTask && tl_current) {
        std::lock_guard<std::mutex> lock(g_mutex);
        if (tl_current->errorText.empty()) tl_current->errorText = "native: uncaught THROW " + text;
        return 1;
    }
    uxb::console_write(text + "\n");
    return 1;
}

// S-163: RND / RND(x) -> [0,1) F64 (x < 0 yeniden tohumla, x = 0 son deger, x > 0 yeni deger).
UXB_RT_API double UXB_RT_CDECL __uxb_rt_rnd_f64(int64_t hasArg, double arg) {
    UxbRng& r = current_rng();
    if (hasArg) {
        if (arg == 0.0) return r.lastValue;
        if (arg < 0.0) r.seed(static_cast<uint64_t>(static_cast<int64_t>(arg)));
    }
    return r.nextF64();
}

// S-163: RANDOMIZE n (hasSeed=1) / RANDOMIZE (zaman tohumu).
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_randomize_seed(int64_t hasSeed, int64_t seed) {
    if (hasSeed) {
        current_rng().seed(static_cast<uint64_t>(seed));
    } else {
        const auto now = std::chrono::high_resolution_clock::now().time_since_epoch().count();
        current_rng().seed(static_cast<uint64_t>(now) ^ 0x9E3779B97F4A7C15ULL);
    }
    return 0;
}
// K6 iptal noktasi: 1 = gorev iptal istendi, lane donmeli (kod uretimi donus yolunu uretir).
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_cancel_point(void) {
    TaskRunV2* t = tl_current;
    if (!t || !t->cancelRequested.load()) return 0;
    std::lock_guard<std::mutex> lock(g_mutex);
    if (t->errorText.empty()) t->errorText = "CANCELLED";
    return 1;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_wait(int64_t handle) {
    {
        std::lock_guard<std::mutex> lock(g_mutex);
        if (!task_at_locked(handle)) runtime_fatal("TASK.WAIT(): bos (NULL) gorev tutamaci");
    }
    wait_finished(handle);
    return 0;
}

static int64_t join_or_result(int64_t handle, const char* what) {
    {
        std::lock_guard<std::mutex> lock(g_mutex);
        if (!task_at_locked(handle)) runtime_fatal(std::string(what) + ": bos (NULL) gorev tutamaci");
    }
    wait_finished(handle);
    std::lock_guard<std::mutex> lock(g_mutex);
    TaskRunV2* t = task_at_locked(handle);
    if (t->state == TS_ERROR || t->state == TS_CANCELLED) {
        t->errorObserved = true;
        runtime_fatal(failure_message_locked(t));
    }
    return result_value_locked(t);
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_join(int64_t handle) { return join_or_result(handle, "TASK.JOIN()"); }
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_result(int64_t handle) { return join_or_result(handle, "TASK.RESULT"); }

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_cancel(int64_t handle) {
    std::lock_guard<std::mutex> lock(g_mutex);
    TaskRunV2* t = task_at_locked(handle);
    if (!t) runtime_fatal("TASK.CANCEL(): bos (NULL) gorev tutamaci");
    if (!is_finished(t->state)) t->cancelRequested.store(true);
    return 0;
}

UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_task_status(int64_t handle) {
    std::lock_guard<std::mutex> lock(g_mutex);
    TaskRunV2* t = task_at_locked(handle);
    if (t && (t->state == TS_ERROR || t->state == TS_CANCELLED)) t->errorObserved = true;
    return hold_task_text(t ? state_name(t->state) : "PENDING");
}

UXB_RT_API const char* UXB_RT_CDECL __uxb_rt_task_error(int64_t handle) {
    std::lock_guard<std::mutex> lock(g_mutex);
    TaskRunV2* t = task_at_locked(handle);
    if (t && !t->errorText.empty()) t->errorObserved = true;
    return hold_task_text(t ? t->errorText : std::string());
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_group_create(void) {
    std::lock_guard<std::mutex> lock(g_mutex);
    g_groups.push_back(std::make_unique<TaskGroupV2>());
    return static_cast<int64_t>(g_groups.size());
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_group_add(int64_t group, int64_t task) {
    std::lock_guard<std::mutex> lock(g_mutex);
    TaskGroupV2* g = group_at_locked(group);
    if (!g) runtime_fatal("TASKGROUP.ADD(): bos (NULL) grup tutamaci");
    if (!task_at_locked(task)) runtime_fatal("TASKGROUP.ADD(): arguman bir TASK olmali");
    g->members.push_back(task);
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_group_join(int64_t group) {
    std::vector<int64_t> members;
    {
        std::lock_guard<std::mutex> lock(g_mutex);
        TaskGroupV2* g = group_at_locked(group);
        if (!g) runtime_fatal("TASKGROUP.JOIN(): bos (NULL) grup tutamaci");
        members = g->members;
    }
    for (int64_t m : members) wait_finished(m);
    // Ilk hatali/iptal uye (ekleme sirasina gore) cagirana yukselir -- AST/MIR ile ayni.
    std::lock_guard<std::mutex> lock(g_mutex);
    for (int64_t m : members) {
        TaskRunV2* t = task_at_locked(m);
        if (t && (t->state == TS_ERROR || t->state == TS_CANCELLED)) {
            t->errorObserved = true;
            runtime_fatal(failure_message_locked(t));
        }
    }
    return 0;
}

// K5: program sonu. normalExit=1: tum gorevleri bekle; 0: bitmemislere iptal iste, sonra bekle.
// Donus: 0 = temiz, 1 = okunmamis gorev hatasi vardi (hata cikisina yazildi; cikis kodu basarisiz olmali).
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_shutdown(int64_t normalExit) {
    uxb::console_flush_current_thread();
    // S-146: ana program kilit tutarken bitebilir (LOCK icinde END); gorevler o kilidi bekliyor olabilir.
    uxb::sync_release_all(uxb::current_task_key());
    std::vector<int64_t> all;
    {
        std::lock_guard<std::mutex> lock(g_mutex);
        if (!g_poolStarted) return 0;
        for (auto& t : g_tasks) {
            if (!normalExit && !is_finished(t->state)) t->cancelRequested.store(true);
            all.push_back(t->id);
        }
    }
    for (int64_t id : all) wait_finished(id);
    int64_t unread = 0;
    {
        std::lock_guard<std::mutex> lock(g_mutex);
        for (auto& t : g_tasks) {
            // Iptal, programin kendi istegidir (hata degil); yalniz okunmamis ERROR raporlanir.
            if (t->state == TS_ERROR && !t->errorObserved) {
                const std::string msg = "okunmamis gorev hatasi (" + t->name + "): " + t->errorText;
                std::fwrite(msg.data(), 1, msg.size(), stderr);
                std::fputc('\n', stderr);
                unread = 1;
            }
        }
        std::fflush(stderr);
        g_stopping = true;
    }
    g_workAvailable.notify_all();
#if defined(_WIN32)
    for (HANDLE w : g_workers) {
        WaitForSingleObject(w, INFINITE);
        CloseHandle(w);
    }
    g_workers.clear();
#else
    for (auto& w : g_workers) {
        if (w.joinable()) w.join();
    }
#endif
    return unread;
}

// S-156: rutin icindeki END. Ana is parcacigindan cagrilir (izolasyon denetimi gorev govdesinde END'i
// reddeder). K5 normal kapanisi: gorevler beklenir, okunmamis hata cikis kodunu 1 yapar.
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_program_end(void) {
    uxb::console_flush_current_thread();
    const int64_t unread = __uxb_rt_task_shutdown(1);
    std::fflush(stdout);
    std::exit(unread ? 1 : 0);
}

// K4: derleyicinin gomdugu isci sayisi; havuz acildiktan sonra etkisizdir.
UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_set_workers(int64_t count) {
    if (count >= 1 && count <= 1024) g_embeddedWorkers.store(static_cast<int>(count));
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_task_worker_count(void) {
    std::lock_guard<std::mutex> lock(g_mutex);
    return g_poolStarted ? g_workerCount : configured_worker_count();
}

namespace uxb {
bool task_pool_active() { return g_poolActive.load(std::memory_order_relaxed); }

int64_t current_task_key() { return tl_current ? tl_current->id : 0; }

void task_pool_block_begin() {
    if (!tl_isWorker) {
        std::lock_guard<std::mutex> lock(g_mutex);
        maybe_add_worker_locked();
        return;
    }
    std::lock_guard<std::mutex> lock(g_mutex);
    S().blockedWorkers++;
    maybe_add_worker_locked();
}

void task_pool_block_end() {
    if (!tl_isWorker) return;
    std::lock_guard<std::mutex> lock(g_mutex);
    S().blockedWorkers--;
}
}  // namespace uxb
