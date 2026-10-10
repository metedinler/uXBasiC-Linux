# uXBasic Linux calistirma klasoru

DURUM: Dogrulanmadi. Bu klasor, FreeBASIC Linux surumuyle derleyiciyi derlemek icin hazirlandi;
derleme ve testler tamamlanmadan calistigi iddia edilmez. Sonuclar dogrulaninca bu dosya guncellenecek.

- `shim/kernel32_shim.c`: Windows `kernel32` cagrilarini (LoadLibraryA, GetProcAddress, FreeLibrary,
  GetModuleFileNameA) `dlopen`/`dlsym`/`dlclose` ile karsilar. Windows DLL FFI cagrilari Linux'ta Windows gibi calismaz.
- `build_linux.sh`: shim'i derler, `src/main.bas` dosyasini `fbc` ile derler (`FBC_PREFIX` ile fbc dizini verilebilir).

Beklenti (kanitlanmadi): yorumlayicilar (AST, MIR), JS hatti ve JSON ciktilari Linux'ta calisabilir;
x64 (NASM/MinGW) uretilen kodu Windows hedeflidir.
