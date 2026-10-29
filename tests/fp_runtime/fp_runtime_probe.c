#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

typedef unsigned char UXB_F80[16];
typedef unsigned char UXB_F128[16];

__declspec(dllimport) int  uxb_f80_size(void);
__declspec(dllimport) int  uxb_f80_storage_size(void);
__declspec(dllimport) void uxb_f80_from_str(const char *src, void *outp);
__declspec(dllimport) void uxb_f80_to_str(const void *a, char *outBuf, int outBytes);
__declspec(dllimport) void uxb_f80_add(const void *a, const void *b, void *outp);

__declspec(dllimport) int  uxb_f128_size(void);
__declspec(dllimport) int  uxb_f128_storage_size(void);
__declspec(dllimport) void uxb_f128_from_str(const char *src, void *outp);
__declspec(dllimport) void uxb_f128_to_str(const void *a, char *outBuf, int outBytes);
__declspec(dllimport) void uxb_f128_add(const void *a, const void *b, void *outp);

int main(void) {
    char buf[256];

    UXB_F80 a80, b80, c80;
    memset(a80, 0, sizeof(a80));
    memset(b80, 0, sizeof(b80));
    memset(c80, 0, sizeof(c80));

    if (uxb_f80_size()!=16 || uxb_f80_storage_size()!=16) return 2;
    printf("f80_size=%d storage=%d\n", uxb_f80_size(), uxb_f80_storage_size());
    uxb_f80_from_str("1.25", a80);
    uxb_f80_from_str("2.50", b80);
    uxb_f80_add(a80, b80, c80);
    memset(buf, 0, sizeof(buf));
    uxb_f80_to_str(c80, buf, sizeof(buf));
    printf("f80_add=%s\n", buf);
    if (fabs(strtod(buf,NULL)-3.75)>1e-12) return 3;

    UXB_F128 a128, b128, c128;
    memset(a128, 0, sizeof(a128));
    memset(b128, 0, sizeof(b128));
    memset(c128, 0, sizeof(c128));

    if (uxb_f128_size()!=16 || uxb_f128_storage_size()!=16) return 4;
    printf("f128_size=%d storage=%d\n", uxb_f128_size(), uxb_f128_storage_size());
    uxb_f128_from_str("1.0000000000000000000000000000000001", a128);
    uxb_f128_from_str("2.0000000000000000000000000000000001", b128);
    uxb_f128_add(a128, b128, c128);
    memset(buf, 0, sizeof(buf));
    uxb_f128_to_str(c128, buf, sizeof(buf));
    printf("f128_add=%s\n", buf);
    if (fabs(strtod(buf,NULL)-3.0)>1e-12) return 5;

    puts("PASS_FP_RUNTIME");
    return 0;
}
