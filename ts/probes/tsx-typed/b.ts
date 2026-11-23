export function f(x: any, y: { a: number }): number {
  const v = x.foo.bar;
  x.call();
  return y.a + `${v}`.length;
}
