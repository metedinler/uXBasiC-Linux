// S-146 Model D (Mete 2026-09-26) -- native kilit tablosu.
// Tasarim: docs/tasarim/UXB_S146_GOREV_PAYLASIMLI_VERI_ONERISI_20260925_TR.md §10.
//
// - Depo basina kilit (tek kuresel mutex YOK): kimlik = derleyicinin lockOrderId'si (global
//   bildirim sirasi, 1..N) ya da MUTEX_NEW'in verdigi (1<<32)+n. Coklu kilit her zaman artan
//   kimlik sirasiyla alinir, ters sirayla birakilir (platformdan bagimsiz sira).
// - Sahip GOREVDIR (anahtar: ana program 0, gorev = gorev kimligi) -- bekleyen is parcacigi
//   kuyruktan baska gorevi kendi uzerinde calistirabildigi icin is parcacigi kimligi yetmez.
// - mode 0 = otomatik deyim kilidi (derleyicinin SYNC_ENTER/LEAVE'i): ayni gorev icin yeniden
//   girilebilir (acik LOCK'un sahipligini tanir). mode 1 = acik LOCK: ayni gorevin ayni kilidi
//   ikinci kez acikca almasi SELF_DEADLOCK.
// - Bekleme grafigi (gorev -> kilit sahibi, gorev -> beklenen gorev): cevrim kapanirsa
//   LOCK_DEADLOCK. Iki tani da olumcul: surec acik iletiyle 1 koduyla biter (yorumlayicilarla ayni
//   metin; TRY ile yakalanmaz, gorev hatasi olarak tutulmaz).

#include "uxb_runtime.h"
#include "uxb_runtime_print.h"

#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

struct LockRec {
    int64_t owner = -1;
    int autoDepth = 0;
    int explicitDepth = 0;
    std::string name;
    std::condition_variable cv;
};

struct WaitEdge {
    int kind = 0;        // 1 = kilit (target = kilit kimligi), 2 = gorev (target = gorev anahtari)
    int64_t target = 0;
};

struct SyncState {
    std::mutex mutex;
    std::unordered_map<int64_t, std::unique_ptr<LockRec>> locks;
    std::unordered_map<int64_t, WaitEdge> edges;
    std::unordered_map<int64_t, int> heldCount;                               // anahtar -> tuttugu kilit sayisi
    std::unordered_map<int64_t, std::vector<std::vector<int64_t>>> explicitStack;
    int64_t explicitEntries = 0;
    int64_t mutexNext = 0;
};

// Surec boyunca yasar (yok edilmez): exit() sirasinda calisan iscilerle yarismasin (task_v2 ile ayni).
SyncState& S() {
    static SyncState* state = new SyncState();
    return *state;
}

[[noreturn]] void sync_fatal(const std::string& message) {
    uxb::console_flush_current_thread();
    std::fflush(stdout);
    std::fputs(message.c_str(), stderr);
    std::fputc('\n', stderr);
    std::fflush(stderr);
    std::exit(1);
}

// Kilit tutulurken cagrilir.
LockRec& rec_locked(int64_t id, const std::string& name) {
    auto& slot = S().locks[id];
    if (!slot) slot = std::make_unique<LockRec>();
    if (slot->name.empty() && !name.empty()) slot->name = name;
    return *slot;
}

std::string label_locked(int64_t id) {
    auto it = S().locks.find(id);
    if (it != S().locks.end() && !it->second->name.empty()) return "'" + it->second->name + "'";
    const int64_t base = int64_t(1) << 32;
    if (id > base) return "MUTEX #" + std::to_string(id - base);
    return "#" + std::to_string(id);
}

// `from` dugumunden bekleme kenarlari izlenerek `me`ye donuluyor mu. Donuluyorsa yol uzerindeki
// ilk kilidin kimligi lockOut'a yazilir (yoksa -1).
bool cycle_locked(int64_t from, int64_t me, int64_t& lockOut) {
    lockOut = -1;
    int64_t cur = from;
    for (int steps = 0; steps < 1000000; ++steps) {
        if (cur == me) return true;
        auto e = S().edges.find(cur);
        if (e == S().edges.end()) return false;
        if (e->second.kind == 1) {
            if (lockOut < 0) lockOut = e->second.target;
            auto l = S().locks.find(e->second.target);
            if (l == S().locks.end() || l->second->owner < 0) return false;
            cur = l->second->owner;
        } else {
            cur = e->second.target;
        }
    }
    return false;
}

[[noreturn]] void deadlock_fatal_locked(int64_t lockId) {
    if (lockId >= 0) {
        sync_fatal("LOCK_DEADLOCK: " + label_locked(lockId) +
                   " kilidini tutan gorev, bu gorevin bitmesini bekliyor (LOCK icinde JOIN/WAIT ile karsilikli bekleme)");
    }
    sync_fatal("TASK_WAIT_CYCLE: gorevler birbirini bekliyor (A.JOIN <-> B.JOIN)");
}

// 1 = alindi (ya da ayni gorevde yeniden girildi), 0 = baska gorevde (beklemeden doner).
bool try_acquire_locked(int64_t key, int64_t id, const std::string& name, bool isExplicit) {
    LockRec& r = rec_locked(id, name);
    if (r.owner == key) {
        if (isExplicit) {
            if (r.explicitDepth > 0) {
                sync_fatal("SELF_DEADLOCK: " + label_locked(id) +
                           " bu gorev tarafindan zaten LOCK ile tutuluyor; ayni kilidi ikinci kez LOCK etmek kendini kilitler");
            }
            r.explicitDepth++;
        } else {
            r.autoDepth++;
        }
        return true;
    }
    if (r.owner >= 0) return false;   // dolu: cagiran bu cagrida aldiklarini birakip bekler
    r.owner = key;
    if (isExplicit) r.explicitDepth = 1; else r.autoDepth = 1;
    S().heldCount[key]++;
    return true;
}

// Dolu kilidin bosalmasini bekler (bu cagrida alinmis kilit tutulmadan). Bekleme grafigi cevrimi
// yalniz ONCEKI deyimlerden tutulan acik LOCK'lar uzerinden kapanabilir: gercek (programci) kilitlenmesi.
void wait_free_locked(std::unique_lock<std::mutex>& lk, int64_t key, int64_t id) {
    LockRec& r = rec_locked(id, "");
    if (r.owner < 0 || r.owner == key) return;
    S().edges[key] = WaitEdge{1, id};
    int64_t cycLock = -1;
    if (cycle_locked(r.owner, key, cycLock)) deadlock_fatal_locked(id);
    uxb::task_pool_block_begin();
    r.cv.wait(lk, [&r, key] { return r.owner < 0 || r.owner == key; });
    uxb::task_pool_block_end();
    S().edges.erase(key);
}

void release_locked(int64_t key, int64_t id, bool isExplicit) {
    auto it = S().locks.find(id);
    if (it == S().locks.end() || it->second->owner != key) {
        sync_fatal("native: ic kilit hatasi: " + label_locked(id) + " bu gorevin degilken birakiliyor");
    }
    LockRec& r = *it->second;
    if (isExplicit) {
        if (r.explicitDepth > 0) r.explicitDepth--;
    } else {
        if (r.autoDepth > 0) r.autoDepth--;
    }
    if (r.autoDepth == 0 && r.explicitDepth == 0) {
        r.owner = -1;
        auto h = S().heldCount.find(key);
        if (h != S().heldCount.end() && --h->second <= 0) S().heldCount.erase(h);
        r.cv.notify_all();
    }
}

// (kimlik, ad) listesi: artan kimlik, tekil. Adlar yalniz statik kimliklere paraleldir.
std::vector<std::pair<int64_t, std::string>> ordered_targets(const int64_t* ids, int64_t count, const char* names) {
    std::vector<std::pair<int64_t, std::string>> out;
    std::vector<std::string> nameList;
    if (names) {
        std::string cur;
        for (const char* p = names; *p; ++p) {
            if (*p == ',') { nameList.push_back(cur); cur.clear(); } else cur.push_back(*p);
        }
        if (!cur.empty() || (names[0] != '\0')) nameList.push_back(cur);
    }
    for (int64_t i = 0; i < count; ++i) {
        out.emplace_back(ids[i], i < static_cast<int64_t>(nameList.size()) ? nameList[static_cast<std::size_t>(i)] : std::string());
    }
    std::sort(out.begin(), out.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
    out.erase(std::unique(out.begin(), out.end(), [](const auto& a, const auto& b) { return a.first == b.first; }), out.end());
    return out;
}

void pop_explicit_entry_locked(int64_t key) {
    auto st = S().explicitStack.find(key);
    if (st == S().explicitStack.end() || st->second.empty()) return;
    std::vector<int64_t> entry = st->second.back();
    st->second.pop_back();
    S().explicitEntries--;
    for (auto it = entry.rbegin(); it != entry.rend(); ++it) release_locked(key, *it, true);
    if (st->second.empty()) S().explicitStack.erase(st);
}

}  // namespace

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_sync_enter(const int64_t* ids, int64_t count, const char* names, int64_t mode) {
    if (!ids || count <= 0) return 0;
    const int64_t key = uxb::current_task_key();
    const bool isExplicit = (mode != 0);
    auto targets = ordered_targets(ids, count, names);
    std::unique_lock<std::mutex> lk(S().mutex);
    // Ya hepsi ya hicbiri: kilitlerden biri doluysa bu cagrida alinanlar birakilir, dolu olan beklenir,
    // bastan denenir. Boylece deyim kilidi hic bir zaman "birini tutup otekini bekleme" durumuna dusmez
    // (ornek: A `LOCK y` icinde x'e dokunur, B tek deyimde x ve y'yi kilitler -- kilitlenme olmaz).
    std::vector<int64_t> taken;
    for (;;) {
        taken.clear();
        int64_t blockedOn = -1;
        for (const auto& t : targets) {
            if (try_acquire_locked(key, t.first, t.second, isExplicit)) {
                taken.push_back(t.first);
            } else {
                blockedOn = t.first;
                break;
            }
        }
        if (blockedOn < 0) break;
        for (auto it = taken.rbegin(); it != taken.rend(); ++it) release_locked(key, *it, isExplicit);
        wait_free_locked(lk, key, blockedOn);
    }
    if (isExplicit) {
        S().explicitStack[key].push_back(taken);
        S().explicitEntries++;
    }
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_sync_leave(const int64_t* ids, int64_t count, int64_t mode) {
    if (!ids || count <= 0) return 0;
    const int64_t key = uxb::current_task_key();
    std::lock_guard<std::mutex> lk(S().mutex);
    if (mode != 0) {
        pop_explicit_entry_locked(key);
        return 0;
    }
    auto targets = ordered_targets(ids, count, nullptr);
    for (auto it = targets.rbegin(); it != targets.rend(); ++it) release_locked(key, it->first, false);
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_lock_mark(void) {
    const int64_t key = uxb::current_task_key();
    std::lock_guard<std::mutex> lk(S().mutex);
    auto st = S().explicitStack.find(key);
    return st == S().explicitStack.end() ? 0 : static_cast<int64_t>(st->second.size());
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_lock_release_to(int64_t mark) {
    const int64_t key = uxb::current_task_key();
    std::lock_guard<std::mutex> lk(S().mutex);
    for (;;) {
        auto st = S().explicitStack.find(key);
        if (st == S().explicitStack.end() || static_cast<int64_t>(st->second.size()) <= mark) break;
        pop_explicit_entry_locked(key);
    }
    return 0;
}

UXB_RT_API int64_t UXB_RT_CDECL __uxb_rt_mutex_new(void) {
    std::lock_guard<std::mutex> lk(S().mutex);
    S().mutexNext++;
    return (int64_t(1) << 32) + S().mutexNext;
}

namespace uxb {

bool sync_holds_any(int64_t key) {
    std::lock_guard<std::mutex> lk(S().mutex);
    return S().heldCount.find(key) != S().heldCount.end();
}

int64_t sync_explicit_total() {
    std::lock_guard<std::mutex> lk(S().mutex);
    return S().explicitEntries;
}

void sync_note_wait_task(int64_t key, int64_t targetKey) {
    std::lock_guard<std::mutex> lk(S().mutex);
    S().edges[key] = WaitEdge{2, targetKey};
    int64_t cycLock = -1;
    if (cycle_locked(targetKey, key, cycLock)) deadlock_fatal_locked(cycLock);
}

void sync_clear_wait(int64_t key) {
    std::lock_guard<std::mutex> lk(S().mutex);
    S().edges.erase(key);
}

void sync_release_all(int64_t key) {
    std::lock_guard<std::mutex> lk(S().mutex);
    while (S().explicitStack.find(key) != S().explicitStack.end()) pop_explicit_entry_locked(key);
    for (auto& kv : S().locks) {
        LockRec& r = *kv.second;
        if (r.owner != key) continue;
        r.owner = -1;
        r.autoDepth = 0;
        r.explicitDepth = 0;
        r.cv.notify_all();
    }
    S().heldCount.erase(key);
    S().edges.erase(key);
}

}  // namespace uxb
