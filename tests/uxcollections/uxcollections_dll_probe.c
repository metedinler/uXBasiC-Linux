#include <stdio.h>
#include <math.h>
#include "../../runtime_ext/uxcollections/uxcollections.h"
#define REQUIRE(condition, code) do { if (!(condition)) return (code); } while (0)
int main(void){
    REQUIRE(uxcollections_version()==1 && uxcollections_uses_glib()==1,2);
    void* l=uxc_list_new(); REQUIRE(l,3); uxc_list_push_f64(l,1.5); uxc_list_push_f64(l,2.5); REQUIRE(uxc_list_count(l)==2 && fabs(uxc_list_get_f64(l,0)-1.5)<1e-12,4); printf("list_count=%lld list0=%.3f\n",(long long)uxc_list_count(l),uxc_list_get_f64(l,0)); uxc_list_free(l);
    void* s=uxc_stack_new(); REQUIRE(s,5); uxc_stack_push_f64(s,7.0); double sp=uxc_stack_pop_f64(s); REQUIRE(fabs(sp-7.0)<1e-12,6); printf("stack_pop=%.3f\n",sp); uxc_stack_free(s);
    void* q=uxc_queue_new(); REQUIRE(q,7); uxc_queue_push_f64(q,3.0); uxc_queue_push_f64(q,4.0); double qp=uxc_queue_pop_f64(q); REQUIRE(fabs(qp-3.0)<1e-12,8); printf("queue_pop=%.3f\n",qp); uxc_queue_free(q);
    void* d=uxc_dict_new(); REQUIRE(d,9); uxc_dict_set_f64(d,"a",9.0); REQUIRE(uxc_dict_has(d,"a") && fabs(uxc_dict_get_f64(d,"a")-9.0)<1e-12,10); printf("dict_has=%d dict_a=%.3f\n",uxc_dict_has(d,"a"),uxc_dict_get_f64(d,"a")); uxc_dict_free(d);
    void* set=uxc_set_new(); REQUIRE(set,11); uxc_set_add(set,"mete"); REQUIRE(uxc_set_contains(set,"mete"),12); printf("set_contains=%d\n",uxc_set_contains(set,"mete")); uxc_set_free(set);
    void* t=uxc_tree_new(); REQUIRE(t,13); uxc_tree_set_f64(t,"b",2.0); uxc_tree_set_f64(t,"a",1.0); REQUIRE(fabs(uxc_tree_get_f64(t,"a")-1.0)<1e-12,14); printf("tree_a=%.3f\n",uxc_tree_get_f64(t,"a")); uxc_tree_free(t);
    puts("PASS_UXCOLLECTIONS");
    return 0;
}
