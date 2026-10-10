#define _GNU_SOURCE
#include <dlfcn.h>
#include <unistd.h>
#include <string.h>
void *LoadLibraryA(const char *n) { return dlopen(n, RTLD_NOW | RTLD_GLOBAL); }
void *GetProcAddress(void *h, const char *s) { return dlsym(h, s); }
int FreeLibrary(void *h) { return h ? dlclose(h) == 0 : 0; }
unsigned GetModuleFileNameA(void *h, char *buf, unsigned n) {
    ssize_t r = readlink("/proc/self/exe", buf, n ? n - 1 : 0);
    if (r < 0) return 0;
    buf[r] = 0; return (unsigned)r;
}
