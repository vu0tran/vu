type Acts = { [k: string]: Function };
declare function actions<A extends Acts>(fn: (self: { n: number }) => A): A;
declare function plain<A extends Acts>(a: A): A;
export const T = actions(() => ({
  a(x: number) {
    const z4: string = this.b;
  },
  b(x: number) {
    this.a(x);
  },
}));
export const U = plain({
  a(x: number) {
    const z5: string = this.b;
  },
  b(x: number) {
  },
});
export const V: Acts = {
  a(x: number) {
    const z6: string = this.b;
  },
  b(x: number) {
  },
};
export const W = actions(() => ({
  a(x: number) {
    const z7: string = this.b;
  },
  b(x: number) {
  },
}));
