#include <stdint.h>

#if defined(_WIN32)
#define UXTEST_API __declspec(dllexport)
#else
#define UXTEST_API __attribute__((visibility("default")))
#endif

typedef struct ux_vec2 {
    float x;
    float y;
} ux_vec2;

typedef union ux_number_bits {
    uint64_t as_u64;
    double as_f64;
} ux_number_bits;

UXTEST_API double uxcabi_vec2_sum(ux_vec2 value) {
    return (double)value.x + (double)value.y;
}

UXTEST_API ux_vec2 uxcabi_vec2_add(ux_vec2 left, ux_vec2 right) {
    ux_vec2 result;
    result.x = left.x + right.x;
    result.y = left.y + right.y;
    return result;
}

UXTEST_API void uxcabi_union_write_u64(ux_number_bits *value, uint64_t bits) {
    if (value) value->as_u64 = bits;
}

UXTEST_API double uxcabi_union_read_f64(const ux_number_bits *value) {
    return value ? value->as_f64 : 0.0;
}
