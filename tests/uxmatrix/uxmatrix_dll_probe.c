#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxmatrix/uxmatrix.h"

static int approx(double a, double b) { return fabs(a-b) < 1e-8; }

int main(void) {
    UXMatrixHandle A = uxmatrix_create(2,2);
    UXMatrixHandle B = uxmatrix_create(2,2);
    if(!A || !B) return 2;
    uxmatrix_set(A,0,0,1); uxmatrix_set(A,0,1,2); uxmatrix_set(A,1,0,3); uxmatrix_set(A,1,1,4);
    uxmatrix_set(B,0,0,5); uxmatrix_set(B,0,1,6); uxmatrix_set(B,1,0,7); uxmatrix_set(B,1,1,8);
    UXMatrixHandle C = uxmatrix_mul(A,B);
    if(!C) return 3;
    printf("C00=%g C01=%g C10=%g C11=%g\n", uxmatrix_get(C,0,0), uxmatrix_get(C,0,1), uxmatrix_get(C,1,0), uxmatrix_get(C,1,1));
    if(!approx(uxmatrix_get(C,0,0),19) || !approx(uxmatrix_get(C,1,1),50)) return 4;
    printf("traceA=%g normA=%g detA=%g\n", uxmatrix_trace(A), uxmatrix_norm_l2(A), uxmatrix_det(A));
    if(!approx(uxmatrix_trace(A),5)||!approx(uxmatrix_norm_l2(A),sqrt(30.0))||!approx(uxmatrix_det(A),-2)) return 5;
    UXMatrixHandle Inv = NULL;
    int inv_ok = uxmatrix_inverse(A, &Inv);
    printf("inverse_status=%d inv=%p\n", inv_ok, Inv);
    if(inv_ok!=1||!Inv) return 6;
    if(Inv) {
        if(!approx(uxmatrix_get(Inv,0,0),-2)||!approx(uxmatrix_get(Inv,0,1),1)||!approx(uxmatrix_get(Inv,1,0),1.5)||!approx(uxmatrix_get(Inv,1,1),-0.5)) return 7;
        uxmatrix_print(Inv);
        uxmatrix_free(Inv);
    }
    uxmatrix_free(A); uxmatrix_free(B); uxmatrix_free(C);
    puts("PASS_UXMATRIX");
    return 0;
}
