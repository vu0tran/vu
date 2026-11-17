// assignments in a conditional expression or a logical one's right side: joined as after if/else
interface O { h?: number }
export function g(u: string, options?: O, z?: string) {
  const t = u ? (options ??= {}) : 1;
  const x: number = options;
  const t2 = u && (z = "a");
  const y: number = z;
  let w: string | number | undefined;
  w ?? (w = 3);
  const q: boolean = w;
  let v: string | undefined;
  v || (v = "s");
  const r: number = v;
}
export function h(a: number | string | null, b: boolean) {
  let x: number | string | undefined;
  const r = b ? (x = 1) : a === null ? (x = "s") : (x = a);
  const y: boolean = x;
  let z = a;
  b && (z = 4);
  const q: boolean = z;
  let k: string | number = "a";
  const m = b ? (k = 2) : 0;
  const kk: boolean = k;
  let e: string[] | undefined;
  (e ||= []).push("a");
  const ee: number = e;
  let o = { p: 1 as number | undefined };
  b ? (o.p = undefined) : 0;
  const oo: string = o.p;
}
