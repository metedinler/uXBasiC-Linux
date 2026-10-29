#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxdataset/uxdataset.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)
int main(void){
    void* ds=uxdataset_create(4,2,1);
    if(!ds) return 2;
    for(int r=0;r<4;r++){
        uxdataset_set_x(ds,r,0,(double)r);
        uxdataset_set_x(ds,r,1,(double)(r+1));
        uxdataset_set_y(ds,r,0,(double)(r%2));
    }
    printf("rows=%d input=%d target=%d\n", uxdataset_row_count(ds), uxdataset_input_dim(ds), uxdataset_target_dim(ds));
    REQUIRE(uxdataset_row_count(ds)==4&&uxdataset_input_dim(ds)==2&&uxdataset_target_dim(ds)==1,3);
    void* sc=uxdataset_scaler_fit_standard(ds);
    REQUIRE(sc,4);
    uxdataset_scaler_transform(sc,ds);
    printf("x00=%.6f\n", uxdataset_get_x(ds,0,0));
    REQUIRE(fabs(uxdataset_get_x(ds,0,0)+1.161895003862225)<1e-9,5);
    void* train=uxdataset_split_train(ds,0.5,1234);
    void* test=uxdataset_split_test(ds,0.5,1234);
    printf("train=%d test=%d\n", uxdataset_row_count(train), uxdataset_row_count(test));
    REQUIRE(train&&test&&uxdataset_row_count(train)==2&&uxdataset_row_count(test)==2,6);
    void* bl=uxdataset_batch_create(ds,2,1,55);
    REQUIRE(bl,7);
    int batches=0,rows=0;
    while(uxdataset_batch_next(bl)){batches++;rows+=uxdataset_batch_rows(bl);printf("batch=%d firstx=%.6f\n",uxdataset_batch_rows(bl),uxdataset_batch_get_x(bl,0,0));}
    REQUIRE(batches==2&&rows==4,8);
    uxdataset_batch_free(bl); uxdataset_free(train); uxdataset_free(test); uxdataset_scaler_free(sc); uxdataset_free(ds);
    puts("PASS_UXDATASET");
    return 0;
}
