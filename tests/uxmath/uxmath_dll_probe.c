#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxmath/uxmath.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void) {
    printf("uxmath_version=%d\n", uxmath_version());
    REQUIRE(uxmath_version()==1001,1);

    void* p = uxmath_vec_create(4);
    if (!p) return 2;
    // p(x) = 1 + 2x + 3x^2
    uxmath_vec_push(p, 1.0);
    uxmath_vec_push(p, 2.0);
    uxmath_vec_push(p, 3.0);
    printf("poly_eval_2=%g\n", uxmath_poly_eval(p, 2.0));
    printf("poly_deriv_2=%g\n", uxmath_poly_derivative_eval(p, 2.0));
    printf("poly_integral_0_1=%g\n", uxmath_poly_integral_eval(p, 0.0, 1.0));
    printf("poly_newton_root_guess_-1=%g\n", uxmath_poly_newton(p, -1.0, 50, 1e-10));

    void* soft = uxmath_vec_create(3);
    uxmath_vec_softmax(p, soft);
    printf("softmax0=%g softmax1=%g softmax2=%g\n", uxmath_vec_get(soft,0), uxmath_vec_get(soft,1), uxmath_vec_get(soft,2));
    uxmath_vec_free(soft);

    void* m = uxmath_mat_create(2, 3);
    void* v = uxmath_vec_create(3);
    void* out = uxmath_vec_create(2);
    if (!m || !v || !out) return 3;
    uxmath_mat_set(m,0,0,1.0); uxmath_mat_set(m,0,1,2.0); uxmath_mat_set(m,0,2,3.0);
    uxmath_mat_set(m,1,0,4.0); uxmath_mat_set(m,1,1,5.0); uxmath_mat_set(m,1,2,6.0);
    uxmath_vec_push(v, 1.0); uxmath_vec_push(v, 1.0); uxmath_vec_push(v, 1.0);
    uxmath_mat_vec_mul(m, v, out);
    printf("matvec0=%g matvec1=%g\n", uxmath_vec_get(out,0), uxmath_vec_get(out,1));
    REQUIRE(fabs(uxmath_poly_eval(p,2.0)-17.0)<1e-12,4);
    REQUIRE(fabs(uxmath_poly_derivative_eval(p,2.0)-14.0)<1e-12,5);
    REQUIRE(fabs(uxmath_poly_integral_eval(p,0.0,1.0)-3.0)<1e-12,6);
    REQUIRE(fabs(uxmath_vec_get(out,0)-6.0)<1e-12&&fabs(uxmath_vec_get(out,1)-15.0)<1e-12,7);

    printf("sigmoid0=%g relu_neg=%g rk4_logistic=%g\n", uxmath_sigmoid(0.0), uxmath_relu(-3.0), uxmath_ode_rk4_logistic(1.0, 0.5, 100.0, 0.0, 10.0, 100));

    uxmath_vec_free(p);
    uxmath_mat_free(m);
    uxmath_vec_free(v);
    uxmath_vec_free(out);
    puts("PASS_UXMATH");
    return 0;
}
