// [x, y] = rhs with x an auto-typed let (let x;): x the element's type with its literals widened,
// as x = v; its context any
declare function f1(): Promise<{ a: number }[]>;
declare function f2(): Promise<ReadonlySet<string>>;
export async function g() {
  let assets;
  let ids: ReadonlySet<string>;
  try {
    [assets, ids] = await Promise.all([f1(), f2()]);
  } catch {
    return null;
  }
  const n: string = assets;
  let x, y;
  [x, y] = [1, 'a'];
  const m: boolean = x;
  const k: boolean = y;
  return ids;
}
