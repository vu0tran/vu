#include <stdio.h>
#include <stdlib.h>
typedef struct N { struct N *l, *r; } N;
static N* make(int d){ N* n=malloc(sizeof(N)); if(d>0){n->l=make(d-1);n->r=make(d-1);} else n->l=n->r=NULL; return n; }
static int check(N* n){ return 1+(n->l?check(n->l)+check(n->r):0); }
static void del(N* n){ if(n->l){del(n->l);del(n->r);} free(n); }
int main(int c,char**v){ int n=c>1?atoi(v[1]):10, mx=n<6?6:n;
 N* t=make(mx+1); printf("stretch tree of depth %d\t check: %d\n",mx+1,check(t)); del(t);
 N* ll=make(mx);
 for(int d=4;d<=mx;d+=2){ int it=1<<(mx-d+4), ck=0; for(int i=0;i<it;i++){N* a=make(d);ck+=check(a);del(a);} printf("%d\t trees of depth %d\t check: %d\n",it,d,ck); }
 printf("long lived tree of depth %d\t check: %d\n",mx,check(ll)); del(ll); }
