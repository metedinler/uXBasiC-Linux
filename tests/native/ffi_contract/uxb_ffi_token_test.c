#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API
#endif

typedef struct test_box { char value[256]; } test_box;
static int g_ready_count = 0;

API int uxfb_runtime_ready(void) { return ++g_ready_count; }
API int uxb_test_ready_count(void) { return g_ready_count; }
API void *uxb_test_open(void) {
    test_box *box = (test_box *)calloc(1, sizeof(test_box));
    if (box) snprintf(box->value, sizeof(box->value), "%s", "initial");
    return box;
}
API int uxb_test_set(void *handle, const char *text) {
    test_box *box = (test_box *)handle;
    if (!box || !text) return 0;
    snprintf(box->value, sizeof(box->value), "%s", text);
    return 1;
}
API const char *uxb_test_get(void *handle) {
    test_box *box = (test_box *)handle;
    return box ? box->value : "";
}
API void uxb_test_free(void *handle) { free(handle); }
API int64_t uxb_test_sum10(int32_t a1,int32_t a2,int32_t a3,int32_t a4,int32_t a5,int32_t a6,int32_t a7,int32_t a8,int32_t a9,int32_t a10) {
    return (int64_t)a1+a2+a3+a4+a5+a6+a7+a8+a9+a10;
}
API double uxb_test_half(int32_t value) { return (double)value + 0.5; }
