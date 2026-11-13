type A = { a: number } & { b: string };
type P = { then(f: (x: number) => void): void } & { c: 1 };
declare function f(): A;
declare function g(): Promise<A>;
declare function h(): P;
async function m() {
  const x = await f();
  const y = await g();
  const s: string = x.a;
  const t: number = y.b;
  return x;
}
async function n() { return await h(); }
export {};
