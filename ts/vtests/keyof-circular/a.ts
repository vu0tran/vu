type Payloads<M> = { [E in keyof M]: unknown };
function f<M extends Payloads<M>>(k: keyof M & string, s: string, n: number, k2: keyof M) {
  const a: keyof M = k;
  const b: keyof M = s;
  const c: keyof M = n;
  const d: keyof M & string = k2;
}
export {};
