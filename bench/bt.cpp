#include <cstdio>
#include <cstdlib>
#include <memory>
struct N { std::unique_ptr<N> l, r; };
static std::unique_ptr<N> make(int d){ auto n=std::make_unique<N>(); if(d>0){n->l=make(d-1);n->r=make(d-1);} return n; }
static int check(const N& n){ return 1+(n.l?check(*n.l)+check(*n.r):0); }
int main(int c,char**v){ int n=c>1?atoi(v[1]):10, mx=n<6?6:n;
 { auto t=make(mx+1); printf("stretch tree of depth %d\t check: %d\n",mx+1,check(*t)); }
 auto ll=make(mx);
 for(int d=4;d<=mx;d+=2){ int it=1<<(mx-d+4), ck=0; for(int i=0;i<it;i++){auto a=make(d);ck+=check(*a);} printf("%d\t trees of depth %d\t check: %d\n",it,d,ck); }
 printf("long lived tree of depth %d\t check: %d\n",mx,check(*ll)); }
