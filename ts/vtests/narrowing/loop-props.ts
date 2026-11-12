// A property not narrowed before a loop that exits only through its head keeps its declared type there
export {};
interface O { p: string | undefined; n: number | null }
declare const o: O;
declare const xs: string[];
function l1() {
  for (const x of xs) { o.p = x; const a: number = o.p; }
  const b: number = o.p;
}
function l2() {
  let i = 0;
  while (i < 3) { const c0: boolean = o.n; o.n = i; i++; }
  const d: boolean = o.n;
}
