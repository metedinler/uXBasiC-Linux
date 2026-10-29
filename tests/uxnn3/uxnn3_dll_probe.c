#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxnn3/uxnn3.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void){
    void* ds=uxnn3_dataset_create(4,2,1);
    if(!ds){puts("dataset fail"); return 2;}
    double x[4][2]={{0,0},{0,1},{1,0},{1,1}};
    double y[4]   ={0,1,1,0};
    for(int r=0;r<4;r++){
        uxnn3_dataset_x_set(ds,r,0,x[r][0]); uxnn3_dataset_x_set(ds,r,1,x[r][1]); uxnn3_dataset_y_set(ds,r,0,y[r]);
    }
    void* net=uxnn3_model_create(2);
    uxnn3_model_add_dense(net,4,UXNN3_ACT_TANH);
    uxnn3_model_add_dense(net,1,UXNN3_ACT_SIGMOID);
    uxnn3_model_init(net,1234,0.0);
    uxnn3_model_set_optimizer(net,UXNN3_OPT_MOMENTUM,0.1,0.9);
    double before=uxnn3_model_eval_mse(net,ds);
    double loss=uxnn3_model_train_dataset(net,ds,2000,1,1,42);
    double after=uxnn3_model_eval_mse(net,ds);
    double acc=uxnn3_model_eval_binary_accuracy(net,ds,0.5);
    printf("before=%.6f loss=%.6f after=%.6f acc=%.3f\n",before,loss,after,acc);
    REQUIRE(isfinite(before)&&isfinite(loss)&&isfinite(after)&&after<before*0.01&&acc>0.99,4);
    REQUIRE(uxnn3_model_save(net,"uxnn3_probe_model.uxn3")==1,5);
    void* loaded=uxnn3_model_load("uxnn3_probe_model.uxn3");
    if(!loaded){puts("load fail"); return 3;}
    printf("loaded_layers=%d output_dim=%d\n",uxnn3_model_layer_count(loaded),uxnn3_model_output_dim(loaded));
    REQUIRE(uxnn3_model_layer_count(loaded)==2&&uxnn3_model_output_dim(loaded)==1,6);
    uxnn3_model_free(loaded);
    uxnn3_model_free(net);
    uxnn3_dataset_free(ds);
    remove("uxnn3_probe_model.uxn3");
    puts("PASS_UXNN3");
    return 0;
}
