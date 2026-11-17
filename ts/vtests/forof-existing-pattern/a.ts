// for ([a, b] of xs) over variables declared before; [a, b] = any
declare const anyv: any;
declare const pairs: [number, string][];
declare const arrs: number[][];
export function f(m: Record<string, [number, string][]>) {
  let index: number;
  let meta: string | number = 1;
  for ([index, meta] of anyv.entries()) {
    const q: boolean = index;
    const w: boolean = meta;
  }
  const w2: boolean = meta;
  for ([index, meta] of pairs) {
    const w3: boolean = meta;
  }
  const w4: boolean = meta;
  let a: number | string = 's', b: number | undefined;
  for ([a, b] of arrs) { const w5: boolean = a; }
  const w6: boolean = a;
  let x: string | number = 1;
  [x] = anyv;
  const w7: boolean = x;
}
