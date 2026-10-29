// S-030 Faz 2A adim 1: gorev ABI v2 calisma zamani stres testi (DLL'siz; kaynak dogrudan derlenir).
// Her kip ayri surecte calisir; olumcul yollar (JOIN hatasi vb.) surec cikis kodu ve stderr ile denetlenir.
// Surucu: run_task_v2_tests.ps1
#include "uxb_runtime.h"

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

namespace {

struct Block2 { int64_t result; int64_t a; int64_t b; };

std::atomic<int> g_maxConcurrent{0};
std::atomic<int> g_running{0};

void note_running() {
    const int now = ++g_running;
    int prev = g_maxConcurrent.load();
    while (now > prev && !g_maxConcurrent.compare_exchange_weak(prev, now)) {}
}

int64_t thunk_add(void* p) {
    note_running();
    Block2* b = static_cast<Block2*>(p);
    std::this_thread::sleep_for(std::chrono::microseconds(200));
    b->result = b->a + b->b;
    --g_running;
    return 0;
}

int64_t thunk_fib(void* p);
int64_t spawn_fib(int64_t n) {
    Block2 blk{0, n, 0};
    return __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_fib), &blk, sizeof(blk), "Fib", 1, 0);
}
// Ic ice SPAWN: her gorev iki alt gorev acip bekler (K4: bekleyen isci kuyruktan is calistirir).
int64_t thunk_fib(void* p) {
    Block2* b = static_cast<Block2*>(p);
    if (b->a < 2) { b->result = b->a; return 0; }
    const int64_t x = spawn_fib(b->a - 1);
    const int64_t y = spawn_fib(b->a - 2);
    b->result = __uxb_rt_task_join(x) + __uxb_rt_task_join(y);
    return 0;
}

thread_local std::string tl_ring;
int64_t thunk_text(void* p) {
    Block2* b = static_cast<Block2*>(p);
    const char* arg = nullptr;
    std::memcpy(&arg, &b->a, sizeof(arg));
    tl_ring = std::string("merhaba ") + (arg ? arg : "");
    const char* out = tl_ring.c_str();          // isci is parcacigina ozel -- runtime kopyalamali
    std::memcpy(&b->result, &out, sizeof(out));
    return 0;
}

int64_t thunk_throw(void* p) {
    (void)p;
    __uxb_rt_task_fail_cstr("patladi");
    return 0;
}

// Iptal edilene kadar (en cok 10 sn) calisan gorev; zaman saatle olculur (uyku cozunurlugune guvenilmez).
int64_t thunk_slow_cancellable(void* p) {
    Block2* b = static_cast<Block2*>(p);
    const auto start = std::chrono::steady_clock::now();
    while (std::chrono::steady_clock::now() - start < std::chrono::seconds(10)) {
        if (__uxb_rt_task_cancel_point()) return 0;
        std::this_thread::yield();
    }
    b->result = 7;
    return 0;
}

// Bulusma: N gorevin HEPSI ayni anda calisiyorsa her biri 1 yazar; biri gelmezse 5 sn sonra 0.
std::atomic<int> g_arrived{0};
int64_t g_barrierSize = 0;
int64_t thunk_barrier(void* p) {
    Block2* b = static_cast<Block2*>(p);
    ++g_arrived;
    const auto start = std::chrono::steady_clock::now();
    while (g_arrived.load() < g_barrierSize) {
        if (std::chrono::steady_clock::now() - start > std::chrono::seconds(5)) { b->result = 0; return 0; }
        std::this_thread::yield();
    }
    b->result = 1;
    return 0;
}

// K9: her gorev satirini PARCA PARCA yazar (her parca ayri calisma zamani cagrisi); satirlar
// baska gorevlerin parcalariyla karismamali. Surucu ciktidaki her satiri denetler.
int64_t thunk_print_line(void* p) {
    Block2* b = static_cast<Block2*>(p);
    for (int line = 0; line < 50; ++line) {
        __uxb_rt_print_cstr("L");
        __uxb_rt_print_i64(b->a);
        for (int part = 0; part < 20; ++part) {
            __uxb_rt_print_cstr(":");
            __uxb_rt_print_i64(b->a);
        }
        __uxb_rt_print_newline();
    }
    __uxb_rt_print_cstr("YARIM");   // satir sonu olmadan biten gorev: gorev bitiminde bosaltilmali
    b->result = 1;
    return 0;
}

// Her seviye ~100 bayt yerel dizi + cerceve; 20000 seviye ~2-3 MB yigin.
int64_t deep(int64_t n) {
    volatile char pad[96];
    pad[0] = static_cast<char>(n);
    if (n == 0) return pad[0];
    return deep(n - 1) + 1 + (pad[0] & 0);
}
int64_t thunk_deep(void* p) {
    Block2* b = static_cast<Block2*>(p);
    b->result = deep(b->a);
    return 0;
}

int fail(const char* what) {
    std::printf("FAIL %s\n", what);
    std::fflush(stdout);
    return 2;
}

}  // namespace

int main(int argc, char** argv) {
    const std::string mode = argc > 1 ? argv[1] : "";

    if (mode == "many") {
        std::vector<int64_t> hs;
        for (int i = 0; i < 1000; ++i) {
            Block2 blk{0, i, 1000};
            hs.push_back(__uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_add), &blk, sizeof(blk), "Add", 1, 0));
        }
        int64_t sum = 0;
        for (int64_t h : hs) sum += __uxb_rt_task_join(h);
        // sum(0..999) + 1000*1000
        if (sum != 499500 + 1000000) return fail("many sum");
        std::printf("many OK sum=%lld workers=%lld maxConcurrent=%d\n", static_cast<long long>(sum),
                    static_cast<long long>(__uxb_rt_task_worker_count()), g_maxConcurrent.load());
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "parallel") {
        // K4 kaniti: isci sayisi kadar gorev GERCEKTEN ayni anda calisir.
        g_barrierSize = __uxb_rt_task_worker_count();
        std::vector<int64_t> hs;
        for (int64_t i = 0; i < g_barrierSize; ++i) {
            Block2 blk{0, 0, 0};
            hs.push_back(__uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_barrier), &blk, sizeof(blk), "Bulus", 1, 0));
        }
        int64_t ok = 0;
        for (int64_t h : hs) ok += __uxb_rt_task_join(h);
        if (ok != g_barrierSize) return fail("parallel: gorevler ayni anda calismadi");
        std::printf("parallel OK workers=%lld\n", static_cast<long long>(g_barrierSize));
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "nested") {
        const int64_t h = spawn_fib(15);
        const int64_t r = __uxb_rt_task_join(h);
        if (r != 610) return fail("nested fib(15)");
        std::printf("nested OK fib15=%lld\n", static_cast<long long>(r));
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "string") {
        std::string owned = "dunya";
        const char* arg = owned.c_str();
        Block2 blk{0, 0, 0};
        std::memcpy(&blk.a, &arg, sizeof(arg));
        const int64_t h = __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_text), &blk, sizeof(blk), "Metin", 3, 1);
        owned = "BOZULDU";   // runtime argumani SPAWN aninda kopyalamis olmali
        const int64_t bits = __uxb_rt_task_join(h);
        const char* res = nullptr;
        std::memcpy(&res, &bits, sizeof(res));
        if (!res || std::string(res) != "merhaba dunya") return fail("string sonuc");
        std::printf("string OK %s status=%s\n", res, __uxb_rt_task_status(h));
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "error_errortext") {
        Block2 blk{0, 0, 0};
        const int64_t h = __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_throw), &blk, sizeof(blk), "Boom", 1, 0);
        __uxb_rt_task_wait(h);
        std::printf("%s|%s\n", __uxb_rt_task_status(h), __uxb_rt_task_error(h));
        return static_cast<int>(__uxb_rt_task_shutdown(1));   // hata okundu -> 0
    }
    if (mode == "error_join") {
        Block2 blk{0, 0, 0};
        const int64_t h = __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_throw), &blk, sizeof(blk), "Boom", 1, 0);
        __uxb_rt_task_join(h);   // olumcul: stderr + cikis kodu 1
        return fail("error_join donmemeliydi");
    }
    if (mode == "error_unread") {
        Block2 blk{0, 0, 0};
        __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_throw), &blk, sizeof(blk), "Boom", 1, 0);
        return static_cast<int>(__uxb_rt_task_shutdown(1));   // K5: okunmamis hata -> 1 + stderr
    }
    if (mode == "cancel") {
        Block2 blk{0, 0, 0};
        const int64_t h = __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_slow_cancellable), &blk, sizeof(blk), "Yavas", 1, 0);
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
        __uxb_rt_task_cancel(h);
        __uxb_rt_task_cancel(h);   // tekrar CANCEL zararsiz
        __uxb_rt_task_wait(h);
        std::printf("%s|%s\n", __uxb_rt_task_status(h), __uxb_rt_task_error(h));
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "group") {
        const int64_t g = __uxb_rt_task_group_create();
        std::vector<int64_t> hs;
        for (int i = 1; i <= 8; ++i) {
            Block2 blk{0, i, i};
            const int64_t h = __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_add), &blk, sizeof(blk), "Add", 1, 0);
            __uxb_rt_task_group_add(g, h);
            hs.push_back(h);
        }
        __uxb_rt_task_group_join(g);
        int64_t sum = 0;
        for (int64_t h : hs) {
            if (std::string(__uxb_rt_task_status(h)) != "DONE") return fail("group: uye bitmemis");
            sum += __uxb_rt_task_result(h);
        }
        if (sum != 72) return fail("group sum");
        std::printf("group OK sum=%lld\n", static_cast<long long>(sum));
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "group_error") {
        const int64_t g = __uxb_rt_task_group_create();
        Block2 blk{0, 1, 1};
        __uxb_rt_task_group_add(g, __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_add), &blk, sizeof(blk), "Add", 1, 0));
        __uxb_rt_task_group_add(g, __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_throw), &blk, sizeof(blk), "Boom", 1, 0));
        __uxb_rt_task_group_join(g);   // olumcul
        return fail("group_error donmemeliydi");
    }
    if (mode == "print_atomic") {
        std::vector<int64_t> hs;
        for (int i = 1; i <= 8; ++i) {
            Block2 blk{0, i, 0};
            hs.push_back(__uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_print_line), &blk, sizeof(blk), "Yazar", 1, 0));
        }
        for (int64_t h : hs) __uxb_rt_task_join(h);
        __uxb_rt_print_newline();
        __uxb_rt_print_cstr("print_atomic BITTI");
        __uxb_rt_print_newline();
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "embedded_workers") {
        // K4: --task-workers N gomulu deger; UXB_TASK_WORKERS ortam degiskeni verilmisse o ustundedir.
        __uxb_rt_task_set_workers(3);
        g_barrierSize = __uxb_rt_task_worker_count();
        std::vector<int64_t> hs;
        for (int64_t i = 0; i < g_barrierSize; ++i) {
            Block2 blk{0, 0, 0};
            hs.push_back(__uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_barrier), &blk, sizeof(blk), "Bulus", 1, 0));
        }
        int64_t ok = 0;
        for (int64_t h : hs) ok += __uxb_rt_task_join(h);
        if (ok != g_barrierSize) return fail("embedded_workers: paralel degil");
        std::printf("embedded_workers OK workers=%lld\n", static_cast<long long>(__uxb_rt_task_worker_count()));
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "deep_recursion") {
        // 8 MB isci yigini: gorev govdesinde ~2 MB'lik ozyineleme (C++ varsayilani 1-2 MB'de tasardi).
        Block2 blk{0, 20000, 0};
        const int64_t h = __uxb_rt_task_spawn(reinterpret_cast<void*>(&thunk_deep), &blk, sizeof(blk), "Derin", 1, 0);
        std::printf("deep_recursion OK depth=%lld\n", static_cast<long long>(__uxb_rt_task_join(h)));
        return static_cast<int>(__uxb_rt_task_shutdown(1));
    }
    if (mode == "null_join") {
        __uxb_rt_task_join(0);
        return fail("null_join donmemeliydi");
    }
    std::printf("bilinmeyen kip\n");
    return 3;
}
