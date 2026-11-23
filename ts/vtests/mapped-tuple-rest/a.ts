declare const xs: Promise<string[]>[];
declare const y: Promise<number>;
async function f() {
  const r = await Promise.all([...xs, y]);
  const n: number = r;
  const q = Promise.all([y, ...xs]);
  const z: string = q;
}
type M<T> = { [P in keyof T]: T[P] extends string ? 1 : 2 };
type A = M<[string, ...number[], string]>;
const a: A = [3];
export {};
