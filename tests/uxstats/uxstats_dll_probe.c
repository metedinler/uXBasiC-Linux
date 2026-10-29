#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxstats/uxstats.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void) {
    void *x = uxstats_vec_create(8);
    void *y = uxstats_vec_create(8);
    if (!x || !y) return 2;

    uxstats_vec_push(x, 1.0); uxstats_vec_push(y, 2.0);
    uxstats_vec_push(x, 2.0); uxstats_vec_push(y, 4.0);
    uxstats_vec_push(x, 3.0); uxstats_vec_push(y, 6.0);
    uxstats_vec_push(x, 4.0); uxstats_vec_push(y, 8.0);

    printf("version=%d\n", uxstats_version());
    printf("count=%d\n", uxstats_vec_count(x));
    printf("mean=%.6f\n", uxstats_vec_mean(x));
    printf("stddev_samp=%.6f\n", uxstats_vec_stddev_samp(x));
    printf("median=%.6f\n", uxstats_vec_median(x));
    printf("p75=%.6f\n", uxstats_vec_percentile(x, 75.0));
    printf("corr=%.6f\n", uxstats_vec_correlation(x, y));
    printf("slope=%.6f\n", uxstats_vec_regression_slope(x, y));
    printf("intercept=%.6f\n", uxstats_vec_regression_intercept(x, y));
    printf("r2=%.6f\n", uxstats_vec_regression_r2(x, y));
    REQUIRE(uxstats_version()==1,3);
    REQUIRE(uxstats_vec_count(x)==4&&fabs(uxstats_vec_mean(x)-2.5)<1e-12,4);
    REQUIRE(fabs(uxstats_vec_median(x)-2.5)<1e-12&&fabs(uxstats_vec_percentile(x,75.0)-3.25)<1e-12,5);
    REQUIRE(fabs(uxstats_vec_correlation(x,y)-1.0)<1e-12,6);
    REQUIRE(fabs(uxstats_vec_regression_slope(x,y)-2.0)<1e-12&&fabs(uxstats_vec_regression_intercept(x,y))<1e-12,7);

    uxstats_vec_free(x);
    uxstats_vec_free(y);
    puts("PASS_UXSTATS");
    return 0;
}
