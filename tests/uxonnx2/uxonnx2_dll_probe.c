#include <stdio.h>
#include <math.h>
#include <string.h>
#include "../../runtime_ext/uxonnx2/uxonnx2.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)
int main(int argc, char **argv) {
    const char *dep = argc > 1 ? argv[1] : "uxb\\dist\\runtime_ext\\deps\\uxonnx2";
    int initialized=uxonnx2_init(dep);
    printf("init=%d\n", initialized);
    REQUIRE(initialized==1,2);
    printf("version=%s\n", uxonnx2_version());
    printf("directml=%d cuda=%d\n", uxonnx2_provider_available(1), uxonnx2_provider_available(2));
    void *t = uxonnx2_tensor_create_2d(UXONNX2_DTYPE_F32, 1, 4);
    if(!t) { printf("tensor failed: %s\n", uxonnx2_last_error()); return 2; }
    uxonnx2_tensor_set_f64(t, 0, 1.25);
    uxonnx2_tensor_set_f64(t, 3, 9.5);
    printf("rank=%lld count=%lld v0=%f v3=%f\n", uxonnx2_tensor_rank(t), uxonnx2_tensor_count(t), uxonnx2_tensor_get_f64(t,0), uxonnx2_tensor_get_f64(t,3));
    uxonnx2_tensor_free(t);
    if(argc > 2) {
        void *s = uxonnx2_session_create_advanced(argv[2], UXONNX2_PROVIDER_CPU, 1, 0, 2);
        printf("session=%p err=%s\n", s, uxonnx2_last_error());
        REQUIRE(s,3);
        printf("inputs=%lld outputs=%lld\n", uxonnx2_session_input_count(s), uxonnx2_session_output_count(s));
        REQUIRE(uxonnx2_session_input_count(s)==1 && uxonnx2_session_output_count(s)==1,4);
        REQUIRE(uxonnx2_session_input_rank(s,0)==2 && uxonnx2_session_input_dim(s,0,0)==3 && uxonnx2_session_input_dim(s,0,1)==2,5);
        char input_name[128],output_name[128];
        snprintf(input_name,sizeof(input_name),"%s",uxonnx2_session_input_name(s,0));
        snprintf(output_name,sizeof(output_name),"%s",uxonnx2_session_output_name(s,0));
        void *input=uxonnx2_tensor_create_2d(UXONNX2_DTYPE_F32,3,2);
        REQUIRE(input,6);
        for(int i=0;i<6;i++) uxonnx2_tensor_set_f64(input,i,(double)(i+1));
        void *result=uxonnx2_run1(s,input_name,input,output_name);
        if(!result){printf("run_error=%s\n",uxonnx2_last_error());return 7;}
        REQUIRE(uxonnx2_result_count(result)==1,8);
        void *output=uxonnx2_result_tensor(result,0);
        REQUIRE(uxonnx2_tensor_count(output)==6 && uxonnx2_tensor_rank(output)==2,8);
        for(int i=0;i<6;i++) REQUIRE(fabs(uxonnx2_tensor_get_f64(output,i)-(double)((i+1)*(i+1)))<1e-6,9);
        printf("inference_first=%.3f last=%.3f\n",uxonnx2_tensor_get_f64(output,0),uxonnx2_tensor_get_f64(output,5));
        uxonnx2_result_free(result);
        uxonnx2_tensor_free(input);
        uxonnx2_session_free(s);
    }
    puts("PASS_UXONNX2");
    return 0;
}
