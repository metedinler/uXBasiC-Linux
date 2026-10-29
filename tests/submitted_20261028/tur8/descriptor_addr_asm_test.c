#include <stddef.h>
#include <stdio.h>
#include <stdint.h>

typedef struct { void *data; int64_t lower; int64_t upper; } Descriptor;
extern void *descriptor_addr_asm(const Descriptor *d, int64_t index, int64_t stride);

static int errors=0, tested=0;
static void check(const char*name, const Descriptor*d, int64_t index,int64_t stride,void*want){
  void *got=descriptor_addr_asm(d,index,stride);
  tested++;
  if(got!=want){fprintf(stderr,"FAIL %-28s idx=%lld stride=%lld expected=%p got=%p\n",name,(long long)index,(long long)stride,want,got);errors++;}
}
int main(void){
  char data[128]={0};
  Descriptor d={data,3,5};
  check("4-byte TYPE lower",&d,3,4,data);
  check("4-byte TYPE middle",&d,4,4,data+4);
  check("4-byte TYPE upper",&d,5,4,data+8);
  check("4-byte TYPE below",&d,2,4,NULL);
  check("4-byte TYPE above",&d,6,4,NULL);
  check("12-byte TYPE lower",&d,3,12,data);
  check("12-byte TYPE middle",&d,4,12,data+12);
  check("12-byte TYPE upper",&d,5,12,data+24);
  check("12-byte TYPE below",&d,2,12,NULL);
  check("12-byte TYPE above",&d,6,12,NULL);
  d.lower=-2; d.upper=0;
  check("negative lower",&d,-2,4,data);
  check("negative middle",&d,-1,4,data+4);
  check("negative upper",&d,0,4,data+8);
  check("negative below",&d,-3,4,NULL);
  check("negative above",&d,1,4,NULL);
  d.data=NULL;d.lower=0;d.upper=0;
  check("null data",&d,0,4,NULL);
  d.data=data;d.lower=5;d.upper=4;
  check("inverted bounds",&d,5,4,NULL);
  check("null descriptor",NULL,0,4,NULL);
  printf("ASM descriptor test: %d/%d PASS\n",tested-errors,tested);
  return errors?1:0;
}
