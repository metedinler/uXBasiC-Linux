#include <stdio.h>
#include <math.h>
#include <string.h>
#include "../../runtime_ext/uxnn/uxnn.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void) {
    printf("version=%d backend=%s\n", uxnn_version(), uxnn_backend());
    uxnn_seed(1234);
    void* net = uxnn_network_create();
    void* l1 = uxnn_layer_dense_create(2, 4, 3);
    void* l2 = uxnn_layer_dense_create(4, 1, 1);
    uxnn_layer_init(l1, 2, 0.0);
    uxnn_layer_init(l2, 2, 0.0);
    if (!uxnn_network_add_layer(net,l1) || !uxnn_network_add_layer(net,l2)) return 2;
    double x[8] = {0,0, 0,1, 1,0, 1,1};
    double y[4] = {0,1,1,0};
    double before = uxnn_network_mse_ptr(net,x,y,4,2,1);
    double after = uxnn_network_train_mse_sgd_ptr(net,x,y,4,2,1,200,0.5);
    double out[1]; uxnn_network_forward_ptr(net,&x[2],out);
    printf("mse_before=%g mse_after=%g sample01=%g layers=%d\n", before, after, out[0], uxnn_network_layer_count(net));
    REQUIRE(uxnn_version()==1 && uxnn_backend() && uxnn_backend()[0],3);
    REQUIRE(isfinite(before) && isfinite(after) && after<before*0.1,4);
    REQUIRE(out[0]>0.9 && uxnn_network_layer_count(net)==2,5);
    uxnn_network_free(net);
    puts("PASS_UXNN");
    return 0;
}
