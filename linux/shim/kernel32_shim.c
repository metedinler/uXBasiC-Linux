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

/* ---- Dosya/bellek API'leri: yalniz baglama icin. Windows'a ozgu yurutulebilir-bellek yolu Linux'ta desteklenmez. ---- */
#include <fcntl.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#define INVALID_HANDLE ((void *)(long)-1)

int CloseHandle(void *h) { return (h && h != INVALID_HANDLE) ? close((int)(long)h) == 0 : 0; }
void *CreateFileA(const char *n, unsigned acc, unsigned share, void *sec, unsigned disp, unsigned flags, void *tmpl) {
    (void)share; (void)sec; (void)flags; (void)tmpl;
    int f = (acc & 0x40000000u) ? ((acc & 0x80000000u) ? O_RDWR : O_WRONLY) : O_RDONLY;
    if (disp == 1 || disp == 2) f |= O_CREAT;      /* CREATE_NEW / CREATE_ALWAYS */
    if (disp == 2 || disp == 5) f |= O_TRUNC;
    int fd = open(n, f, 0644);
    return fd < 0 ? INVALID_HANDLE : (void *)(long)fd;
}
/* Eslemeler desteklenmiyor: basarisizlik (NULL) doner. */
void *CreateFileMappingA(void *f, void *s, unsigned p, unsigned hi, unsigned lo, const char *n) { (void)f;(void)s;(void)p;(void)hi;(void)lo;(void)n; return 0; }
void *MapViewOfFile(void *h, unsigned a, unsigned hi, unsigned lo, unsigned long n) { (void)h;(void)a;(void)hi;(void)lo;(void)n; return 0; }
int UnmapViewOfFile(const void *p) { (void)p; return 0; }
unsigned GetTempPathA(unsigned n, char *buf) {
    const char *t = "/tmp/"; unsigned l = (unsigned)strlen(t);
    if (n > l) memcpy(buf, t, l + 1);
    return l;
}
unsigned GetTempFileNameA(const char *path, const char *prefix, unsigned unique, char *out) {
    (void)unique;
    snprintf(out, 260, "%s%sXXXXXX", path, prefix ? prefix : "");
    int fd = mkstemp(out);
    if (fd < 0) return 0;
    close(fd);
    return 1;
}
/* Bir sayfa kadar okuma/yazma denemesi: write(2) EFAULT dondururse gecersiz. */
static int bad_ptr(const void *p, unsigned long n, int wr) {
    int pf[2]; char tmp;
    if (!p || !n) return 0;
    if (pipe(pf) < 0) return 1;
    int bad = 0;
    for (unsigned long i = 0; i < n && !bad; i += 4096) {
        const char *q = (const char *)p + i;
        if (wr) { /* yazma: pipe'tan okuyup hedefe kopyalamayi dene */
            if (write(pf[1], "x", 1) != 1 || read(pf[0], (void *)q, 1) != 1) bad = 1;
        } else if (write(pf[1], q, 1) != 1) bad = 1;
        else (void)read(pf[0], &tmp, 1);
    }
    close(pf[0]); close(pf[1]);
    return bad;
}
int IsBadReadPtr(const void *p, unsigned long n) { return bad_ptr(p, n, 0); }
int IsBadWritePtr(void *p, unsigned long n) { return bad_ptr(p, n, 1); }
