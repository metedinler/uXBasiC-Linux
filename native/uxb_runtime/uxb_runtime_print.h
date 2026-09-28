#pragma once
// S-030 Faz 2A (K9: tek PRINT atomik) -- calisma zamani ici, disa acik degil.
// Gorev havuzu hic acilmadiysa konsol ciktisi eskisi gibi dogrudan yazilir. Havuz acildiktan sonra
// her is parcacigi satirini kendi tamponunda biriktirir; satir sonu ('\n') gelince satir(lar) tek
// kilit altinda yazilir. Yarim satir INPUT/konsol komutlari oncesinde, gorev bitiminde, kapanista ve
// olumcul calisma zamani hatasinda bosaltilir.
#include <cstdint>
#include <string>

namespace uxb {

bool task_pool_active();                 // uxb_runtime_task_v2.cpp
void console_write(const std::string& text);   // uxb_runtime_mir.cpp
void console_flush_current_thread();           // uxb_runtime_mir.cpp

// S-146 Model D -- gorev calisma zamani ile kilit tablosu arasindaki kancalar.
// Kilit sirasi: kilit tablosu mutex'i -> gorev mutex'i. Gorev kodu, kendi mutex'ini tutarken
// kilit tablosu fonksiyonlarini CAGIRMAZ.
int64_t current_task_key();              // uxb_runtime_task_v2.cpp: 0 = ana program, gorev = kimlik
void task_pool_block_begin();            // uxb_runtime_task_v2.cpp: isci bekleyecek (gerekirse ek isci acilir)
void task_pool_block_end();
bool sync_holds_any(int64_t key);        // uxb_runtime_sync.cpp
int64_t sync_explicit_total();
void sync_note_wait_task(int64_t key, int64_t targetKey);   // bekleme grafigi; cevrim = olumcul tani
void sync_clear_wait(int64_t key);
void sync_release_all(int64_t key);      // gorev bittiginde / program sonunda

}  // namespace uxb
