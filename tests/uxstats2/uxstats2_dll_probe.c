#include <math.h>
#include <stdio.h>
#include "../../runtime_ext/uxstats2/uxstats2.h"

static int push(void *handle, double value) {
    return uxstats2_vec_push(handle, value) == 1;
}

static int probability(double value) {
    return isfinite(value) && value >= 0.0 && value <= 1.0;
}

#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void) {
    const double xv[] = {1.0,2.0,3.0,4.0,5.0,6.0,1.5,2.5,3.5,4.5,5.5,6.5};
    const double yv[] = {2.1,4.5,5.8,8.7,9.9,12.4,4.0,6.1,7.9,10.2,12.3,14.0};
    const double ev[] = {0.40,-0.20,0.10,-0.30,0.25,-0.15,0.05,0.20,-0.10,0.30,-0.25,0.12};
    const double av[] = {1.20,-0.40,0.80,-1.00,0.30,1.10,-0.70,0.50,-0.20,0.90,-0.60,0.10};
    const int count = (int)(sizeof(xv) / sizeof(xv[0]));
    void *x=uxstats2_vec_create(count), *y=uxstats2_vec_create(count);
    void *g=uxstats2_vec_create(count), *e=uxstats2_vec_create(count);
    void *adf=uxstats2_vec_create(count);
    REQUIRE(x && y && g && e && adf, 2);
    for(int i=0;i<count;i++) {
        REQUIRE(push(x,xv[i]) && push(y,yv[i]) && push(g,i<6?1.0:2.0), 3);
        REQUIRE(push(e,ev[i]) && push(adf,av[i]), 4);
    }

    double one_t=uxstats2_one_sample_t_p(x,4.0);
    double welch=uxstats2_welch_t_p(x,y);
    double pooled=uxstats2_pooled_t_p(x,y);
    double paired=uxstats2_paired_t_p(x,y);
    double one_z=uxstats2_one_sample_z_p(x,4.0,2.0);
    double prop=uxstats2_one_prop_z_p(55,100,0.50);
    double fvar=uxstats2_f_variance_p(x,y);
    double chisq=uxstats2_chisq_2x2_p(10,20,20,10);
    double anova_f=uxstats2_anova_oneway_f(x,g), anova_p=uxstats2_anova_oneway_p(x,g);
    double bonf=uxstats2_posthoc_bonferroni_t_p(x,g,1.0,2.0,1);
    double tukey=uxstats2_posthoc_tukey_q(x,g,1.0,2.0);
    double scheffe=uxstats2_posthoc_scheffe_f(x,g,1.0,2.0);
    double cov=uxstats2_covariance_samp(x,y), corr=uxstats2_correlation(x,y), vif=uxstats2_vif_pair(x,y);
    double slope=uxstats2_regression_slope(x,y), r2=uxstats2_regression_r2(x,y), reg_p=uxstats2_regression_f_p(x,y);
    double dw=uxstats2_durbin_watson(e), bg_p=uxstats2_breusch_godfrey_p(e,1);
    double adf_stat=uxstats2_adf_stat(adf), adf_p=uxstats2_adf_p_approx(adf);
    double ancova_p=uxstats2_ancova_binary_p(y,x,g,1.0,2.0);
    double hotelling_p=uxstats2_hotelling_p_2d(x,y,g,1.0,2.0);

    REQUIRE(uxstats2_version()==2, 5);
    REQUIRE(probability(one_t) && probability(welch) && probability(pooled) && probability(paired), 6);
    REQUIRE(probability(one_z) && probability(prop) && probability(fvar) && probability(chisq), 7);
    REQUIRE(isfinite(anova_f) && probability(anova_p), 8);
    REQUIRE(probability(bonf) && isfinite(tukey) && isfinite(scheffe), 9);
    REQUIRE(isfinite(cov) && isfinite(corr) && fabs(corr)<1.0 && isfinite(vif), 10);
    REQUIRE(isfinite(slope) && probability(r2) && probability(reg_p), 11);
    REQUIRE(isfinite(dw) && probability(bg_p), 12);
    REQUIRE(isfinite(adf_stat) && probability(adf_p), 13);
    REQUIRE(probability(ancova_p) && probability(hotelling_p), 14);

    printf("version=%d\n",uxstats2_version());
    printf("one_t_p=%.6f welch_p=%.6f pooled_p=%.6f paired_p=%.6f\n",one_t,welch,pooled,paired);
    printf("z_p=%.6f prop_p=%.6f fvar_p=%.6f chisq2x2_p=%.6f\n",one_z,prop,fvar,chisq);
    printf("anova_f=%.6f p=%.6f bonf=%.6f tukey_q=%.6f scheffe=%.6f\n",anova_f,anova_p,bonf,tukey,scheffe);
    printf("cov=%.6f corr=%.6f vif=%.6f slope=%.6f r2=%.6f reg_p=%.6f\n",cov,corr,vif,slope,r2,reg_p);
    printf("dw=%.6f bg_p=%.6f adf=%.6f adf_p=%.6f ancova_p=%.6f hotelling_p=%.6f\n",dw,bg_p,adf_stat,adf_p,ancova_p,hotelling_p);
    puts("PASS_UXSTATS2");

    uxstats2_vec_free(x); uxstats2_vec_free(y); uxstats2_vec_free(g);
    uxstats2_vec_free(e); uxstats2_vec_free(adf);
    return 0;
}
