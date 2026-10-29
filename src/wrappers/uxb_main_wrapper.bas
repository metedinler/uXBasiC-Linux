' S-666 (x86 emeklilik, Asama 4): 32 bit (x86) derleme emekli edildi. Kaynak agac 64 bit isaretci kodu tasir
' (string_pin.fbs, runtime_memory.fbs ...) ve calisma zamani yalniz Win64 MS ABI konusur; fbc32 ile derleme
' baska hatalardan once bu acik iletiyle baslar.
#Ifndef __FB_64BIT__
#Error "uXBasic: 32 bit (x86) derleme emekli edildi (S-666); 64 bit fbc (fbc64) ile derleyin"
#EndIf

#include once "../hooks/uxb_global_noop_hook.fbs"

' Primary compile entry still uses canonical source tree.
#include once "../main.bas"
