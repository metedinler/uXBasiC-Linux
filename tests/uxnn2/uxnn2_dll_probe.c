#include <stdio.h>
#include <math.h>
#include <string.h>
#include "../../runtime_ext/uxnn2/uxnn2.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)
int main(void){
    uxnn2_seed(1234);
    void* n=uxnn2_network_create(2);
    uxnn2_network_add_dense(n,4,2);
    uxnn2_network_add_dense(n,1,1);
    uxnn2_network_init(n,2,0.0);
    uxnn2_set_optimizer(n,2,0.05);
    uxnn2_set_optimizer_params(n,0.9,0.999,1e-8,0.0);
    double x[8]={0,0, 0,1, 1,0, 1,1};
    double y[4]={0,1,1,0};
    double loss=uxnn2_train_array_mse_ptr(n,x,y,4,2000,1);
    double out[1], predicted[4];
    for(int i=0;i<4;i++){uxnn2_forward_ptr(n,x+i*2,out); predicted[i]=out[0]; printf("xor%d=%f\n",i,out[0]);}
    printf("loss=%f layers=%d outdim=%d\n",loss,uxnn2_network_layer_count(n),uxnn2_network_output_dim(n));
    REQUIRE(uxnn2_version()==2 && strstr(uxnn2_backend(),"training core")!=NULL,2);
    REQUIRE(loss<0.01 && predicted[0]<0.1 && predicted[1]>0.9 && predicted[2]>0.9 && predicted[3]<0.1,3);
    REQUIRE(uxnn2_network_layer_count(n)==2 && uxnn2_network_input_dim(n)==2 && uxnn2_network_output_dim(n)==1,4);
    REQUIRE(uxnn2_save(n,"uxb/dist/runtime_ext/uxnn2_xor.uxn2")==1,5);
    uxnn2_network_free(n);
    void* m=uxnn2_load("uxb/dist/runtime_ext/uxnn2_xor.uxn2");
    if(!m) return 6;
    uxnn2_forward_ptr(m,x+2,out); printf("loaded=%f\n",out[0]);
    REQUIRE(fabs(out[0]-predicted[1])<1e-12,7);
    uxnn2_network_free(m);
    remove("uxb/dist/runtime_ext/uxnn2_xor.uxn2");
    puts("PASS_UXNN2");
    return 0;
}
