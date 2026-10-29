#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxtensor/uxtensor.h"

int main(void) {
    printf("backend=%s\n", uxtensor_backend());
    void* a = uxtensor_create2d_f64(2, 3);
    void* b = uxtensor_create2d_f64(3, 2);
    if (!a || !b) return 2;
    double v = 1.0;
    for (long long r=0; r<2; ++r) for (long long c=0; c<3; ++c) uxtensor_set2d_f64(a, r, c, v++);
    v = 1.0;
    for (long long r=0; r<3; ++r) for (long long c=0; c<2; ++c) uxtensor_set2d_f64(b, r, c, v++);
    void* c = uxtensor_matmul2d_f64(a, b);
    if (!c) return 3;
    printf("c00=%g\n", uxtensor_get2d_f64(c, 0, 0));
    printf("c11=%g\n", uxtensor_get2d_f64(c, 1, 1));
    printf("sum=%g\n", uxtensor_sum_f64(c));
    if(fabs(uxtensor_get2d_f64(c,0,0)-22.0)>1e-12) return 4;
    if(fabs(uxtensor_get2d_f64(c,1,1)-64.0)>1e-12) return 5;
    if(fabs(uxtensor_sum_f64(c)-163.0)>1e-12) return 6;
    uxtensor_free(a); uxtensor_free(b); uxtensor_free(c);
    puts("PASS_UXTENSOR");
    return 0;
}
