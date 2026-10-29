#include <stdio.h>
#include <math.h>
#include <string.h>
#include "../../runtime_ext/uxonnx/uxonnx.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)

int main(int argc, char **argv) {
    const char *dep_dir = argc > 1 ? argv[1] : "uxb\\dist\\runtime_ext\\deps\\uxonnx";
    if (!uxonnx_global_init(dep_dir)) {
        printf("INIT_ERROR=%s\n", uxonnx_last_error(NULL));
        return 2;
    }
    printf("ORT_VERSION=%s\n", uxonnx_runtime_version());
    void *t = uxonnx_tensor_create_2d_f32(1, 3);
    if (!t) return 3;
    uxonnx_tensor_set_f32(t, 0, 1.0);
    uxonnx_tensor_set_f32(t, 1, 2.0);
    uxonnx_tensor_set_f32(t, 2, 3.0);
    printf("TENSOR_COUNT=%lld FIRST=%.3f LAST=%.3f\n", uxonnx_tensor_count(t), uxonnx_tensor_get_f32(t,0), uxonnx_tensor_get_f32(t,2));
    uxonnx_tensor_free(t);
    if (argc > 2) {
        void *s = uxonnx_session_create(argv[2], 1);
        if (!s) { printf("SESSION_ERROR=%s\n", uxonnx_last_error(NULL)); return 4; }
        printf("INPUTS=%lld OUTPUTS=%lld\n", uxonnx_input_count(s), uxonnx_output_count(s));
        char input_name[128],output_name[128];
        snprintf(input_name,sizeof(input_name),"%s",uxonnx_input_name(s,0));
        snprintf(output_name,sizeof(output_name),"%s",uxonnx_output_name(s,0));
        printf("INPUT0=%s OUTPUT0=%s\n",input_name,output_name);
        REQUIRE(uxonnx_input_count(s)==1 && uxonnx_output_count(s)==1,5);
        void *input=uxonnx_tensor_create_2d_f32(3,2);
        REQUIRE(input,6);
        for(int i=0;i<6;i++) uxonnx_tensor_set_f32(input,i,(double)(i+1));
        void *output=uxonnx_run1_f32(s,input_name,input,output_name);
        if(!output){printf("RUN_ERROR=%s\n",uxonnx_last_error(s));return 7;}
        REQUIRE(uxonnx_tensor_count(output)==6 && uxonnx_tensor_rank(output)==2,8);
        for(int i=0;i<6;i++) REQUIRE(fabs(uxonnx_tensor_get_f32(output,i)-(double)((i+1)*(i+1)))<1e-6,9);
        printf("INFERENCE_FIRST=%.3f LAST=%.3f\n",uxonnx_tensor_get_f32(output,0),uxonnx_tensor_get_f32(output,5));
        uxonnx_tensor_free(output);
        uxonnx_tensor_free(input);
        uxonnx_session_free(s);
    }
    puts("PASS_UXONNX");
    return 0;
}
