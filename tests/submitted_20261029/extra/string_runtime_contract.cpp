#include "../../../native/uxb_runtime/uxb_runtime.h"
#include <atomic>
#include <cstdio>
#include <cstring>
#include <string>
#include <thread>

int main() {
    const char* first = nullptr;
    const char* second = nullptr;
    const char* joined = __uxb_rt_str_concat("A", __uxb_rt_chr(0));
    joined = __uxb_rt_str_concat(joined, "Z");
    if (__uxb_rt_str_store(&first, joined) != 1) return 1;
    if (__uxb_rt_str_store(&second, first) != 1) return 2;
    if (__uxb_rt_str_release(&first) != 1 || first != nullptr) return 3;
    if (__uxb_rt_strlen(second) != 3 || std::memcmp(second, "A\0Z", 3)) return 4;
    const char* identity = second;
    if (__uxb_rt_str_store(&second, second) != 1 || identity != second) return 5;
    const char* slots[128]{};
    for (auto& slot : slots) {
        __uxb_rt_str_i64(77);
        if (__uxb_rt_str_store(&slot, second) != 1) return 6;
    }
    if (__uxb_rt_str_release(&second) != 1) return 7;
    for (auto& slot : slots) {
        if (__uxb_rt_strlen(slot) != 3 || std::memcmp(slot, "A\0Z", 3)) return 8;
        if (__uxb_rt_str_release(&slot) != 1 || __uxb_rt_str_release(&slot) != 0) return 9;
    }

    std::atomic<int> failures{0}, completed{0};
    auto worker = [&] {
        const char* owned = nullptr;
        for (int i = 0; i < 4096; ++i) {
            std::string expected = "worker:" + std::to_string(i) + std::string(1, '\0') + "Z";
            const char* value = __uxb_rt_str_concat("worker:", __uxb_rt_str_i64(i));
            value = __uxb_rt_str_concat(value, __uxb_rt_chr(0));
            value = __uxb_rt_str_concat(value, "Z");
            if (__uxb_rt_str_store(&owned, value) != 1 ||
                __uxb_rt_strlen(owned) != static_cast<int64_t>(expected.size()) ||
                std::memcmp(owned, expected.data(), expected.size())) ++failures;
            if (__uxb_rt_str_release(&owned) != 1 || owned != nullptr) ++failures;
            ++completed;
        }
    };
    std::thread a(worker), b(worker);
    a.join(); b.join();
    if (failures || completed != 8192) return 10;
    std::puts("PASS: 128 owned NUL snapshots, self-store, repeated release, 8192 operations on two OS threads");
    return 0;
}
