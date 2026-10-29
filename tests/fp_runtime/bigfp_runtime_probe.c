#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "../../runtime_ext/bigfp/uxb_bigfp.h"

int main(void) {
    char buf[512];

    void *a = uxb_bigf_init(256), *b = uxb_bigf_init(256), *c = uxb_bigf_init(256);
    if (!a || !b || !c) return 2;
    uxb_bigf_from_str("1.25", a);
    uxb_bigf_from_str("2.50", b);
    uxb_bigf_add(a,b,c);
    memset(buf,0,sizeof(buf)); uxb_bigf_to_str(c,buf,sizeof(buf));
    printf("bigf_add=%s\n", buf);
    if (fabs(strtod(buf,NULL)-3.75)>1e-12) return 5;
    uxb_bigf_free(a); uxb_bigf_free(b); uxb_bigf_free(c);

    void *d1 = uxb_bigd_init(80), *d2 = uxb_bigd_init(80), *d3 = uxb_bigd_init(80);
    if (!d1 || !d2 || !d3) return 3;
    uxb_bigd_from_str("1.10", d1);
    uxb_bigd_from_str("2.20", d2);
    uxb_bigd_add(d1,d2,d3);
    memset(buf,0,sizeof(buf)); uxb_bigd_to_str(d3,buf,sizeof(buf));
    printf("bigd_add=%s\n", buf);
    if (fabs(strtod(buf,NULL)-3.3)>1e-12) return 6;
    uxb_bigd_free(d1); uxb_bigd_free(d2); uxb_bigd_free(d3);

    void *x = uxb_ball_init(256), *y = uxb_ball_init(256), *z = uxb_ball_init(256);
    if (!x || !y || !z) return 4;
    uxb_ball_from_str("1.0", x);
    uxb_ball_from_str("2.0", y);
    uxb_ball_add(x,y,z);
    memset(buf,0,sizeof(buf)); uxb_ball_to_str(z,buf,sizeof(buf));
    printf("ball_add=%s\n", buf);
    if (strncmp(buf,"3 +/- 0",7)!=0) return 7;
    uxb_ball_free(x); uxb_ball_free(y); uxb_ball_free(z);
    puts("PASS_BIGFP_RUNTIME");
    return 0;
}
