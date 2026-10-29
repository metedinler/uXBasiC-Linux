#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxaimath/uxaimath.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)
int main(void) {
    double x[4] = {-1.0, 0.0, 1.0, 2.0};
    double y[4] = {0};
    uxaimath_softmax_f64(x, y, 4);
    double softmax_sum = y[0]+y[1]+y[2]+y[3];
    REQUIRE(uxaimath_version() == 1, 2);
    REQUIRE(uxaimath_backend() && uxaimath_backend()[0], 3);
    REQUIRE(fabs(uxaimath_sigmoid(0.0)-0.5) < 1e-12, 4);
    REQUIRE(fabs(softmax_sum-1.0) < 1e-12, 5);
    printf("backend=%s\n", uxaimath_backend());
    printf("sigmoid0=%f\n", uxaimath_sigmoid(0.0));
    printf("softmax_sum=%f\n", softmax_sum);
    double yt[3] = {1.0,0.0,1.0};
    double yp[3] = {0.9,0.2,0.7};
    double mse = uxaimath_mse_f64(yt, yp, 3);
    REQUIRE(fabs(mse-0.04666666666666667) < 1e-12, 6);
    printf("mse=%f\n", mse);
    double w[6] = {1,2,3,4,5,6};
    double b[2] = {0.5, -0.5};
    double in[3] = {1,1,1};
    double out[2] = {0};
    uxaimath_dense_forward_f64(in,w,b,out,3,2);
    REQUIRE(fabs(out[0]-6.5) < 1e-12 && fabs(out[1]-14.5) < 1e-12, 7);
    printf("dense=%f,%f\n", out[0], out[1]);
    puts("PASS_UXAIMATH");
    return 0;
}
