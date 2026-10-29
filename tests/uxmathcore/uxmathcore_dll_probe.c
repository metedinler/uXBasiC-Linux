#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxmathcore/uxmathcore.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void) {
    printf("version=%d\n", uxmathcore_version());
    REQUIRE(uxmathcore_version()==1100,1);
    void* a = uxmathcore_buffer_create(UXMC_TYPE_F64, 0);
    void* b = uxmathcore_buffer_create(UXMC_TYPE_F64, 0);
    void* out = uxmathcore_buffer_create(UXMC_TYPE_F64, 0);
    if (!a || !b || !out) return 2;
    uxmathcore_buffer_push_f64(a, 1.0);
    uxmathcore_buffer_push_f64(a, 2.0);
    uxmathcore_buffer_push_f64(a, 3.0);
    uxmathcore_buffer_push_f64(b, 10.0);
    uxmathcore_buffer_push_f64(b, 20.0);
    uxmathcore_buffer_push_f64(b, 30.0);
    if (!uxmathcore_vec_add_f64(a, b, out)) return 3;
    double v = 0.0;
    uxmathcore_buffer_get_f64(out, 2, &v);
    REQUIRE(fabs(v-33.0)<1e-12,5);
    printf("add_out_2=%g\n", v);
    printf("dot=%g\n", uxmathcore_vec_dot_f64_value(a, b));
    printf("l2=%g\n", uxmathcore_vec_l2_norm_f64_value(a));
    void* i64 = uxmathcore_buffer_cast_handle(a, UXMC_TYPE_I64);
    if (!i64) return 4;
    long long iv = 0;
    uxmathcore_buffer_get_i64(i64, 1, &iv);
    REQUIRE(iv==2,6);
    REQUIRE(fabs(uxmathcore_vec_dot_f64_value(a,b)-140.0)<1e-12,7);
    printf("cast_i64_1=%lld\n", iv);
    uxmathcore_buffer_free(i64);
    uxmathcore_buffer_free(a);
    uxmathcore_buffer_free(b);
    uxmathcore_buffer_free(out);
    puts("PASS_UXMATHCORE");
    return 0;
}
