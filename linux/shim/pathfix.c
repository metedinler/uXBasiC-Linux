/* LD_PRELOAD: yol arguman icindeki '\' karakterini '/' yapar (uXBasic Windows ayraclariyla yol uretir).
 * Kullanim: LD_PRELOAD=linux/out/libpathfix.so ./uxbasic ...   (linux/run_uxb.sh bunu yapar)
 * Kapsam: yalniz asagidaki libc cagrilari; system()/popen() komut dizeleri CEVRILMEZ. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <fcntl.h>
#include <dirent.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <limits.h>

static const char *fix(const char *p, char *buf) {
    if (!p || !strchr(p, '\\')) return p;
    size_t i = 0;
    for (; p[i] && i < PATH_MAX - 1; i++) buf[i] = p[i] == '\\' ? '/' : p[i];
    buf[i] = 0;
    return buf;
}
#define NEXT(name) static __typeof__(&name) real; if (!real) real = dlsym(RTLD_NEXT, #name)

int mkdir(const char *p, mode_t m) { char b[PATH_MAX]; NEXT(mkdir); return real(fix(p, b), m); }
int open(const char *p, int f, ...) {
    char b[PATH_MAX]; NEXT(open); mode_t m = 0;
    if (f & (O_CREAT | O_TMPFILE)) { va_list a; va_start(a, f); m = va_arg(a, mode_t); va_end(a); }
    return real(fix(p, b), f, m);
}
int open64(const char *p, int f, ...) {
    char b[PATH_MAX]; NEXT(open64); mode_t m = 0;
    if (f & (O_CREAT | O_TMPFILE)) { va_list a; va_start(a, f); m = va_arg(a, mode_t); va_end(a); }
    return real(fix(p, b), f, m);
}
FILE *fopen(const char *p, const char *m) { char b[PATH_MAX]; NEXT(fopen); return real(fix(p, b), m); }
FILE *fopen64(const char *p, const char *m) { char b[PATH_MAX]; NEXT(fopen64); return real(fix(p, b), m); }
int stat(const char *p, struct stat *s) { char b[PATH_MAX]; NEXT(stat); return real(fix(p, b), s); }
int lstat(const char *p, struct stat *s) { char b[PATH_MAX]; NEXT(lstat); return real(fix(p, b), s); }
int access(const char *p, int m) { char b[PATH_MAX]; NEXT(access); return real(fix(p, b), m); }
DIR *opendir(const char *p) { char b[PATH_MAX]; NEXT(opendir); return real(fix(p, b)); }
int unlink(const char *p) { char b[PATH_MAX]; NEXT(unlink); return real(fix(p, b)); }
int rmdir(const char *p) { char b[PATH_MAX]; NEXT(rmdir); return real(fix(p, b)); }
int remove(const char *p) { char b[PATH_MAX]; NEXT(remove); return real(fix(p, b)); }
int chdir(const char *p) { char b[PATH_MAX]; NEXT(chdir); return real(fix(p, b)); }
int rename(const char *a, const char *c) { char b1[PATH_MAX], b2[PATH_MAX]; NEXT(rename); return real(fix(a, b1), fix(c, b2)); }
