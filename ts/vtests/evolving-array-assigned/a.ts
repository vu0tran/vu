// let x = [] assigned an array: that array's type there (not evolving), the join reduced by subtypes
enum M { A = 'A', B = 'B' }
declare const markets: M[] | undefined;
export function g() {
  let keys = [];
  if (markets === undefined) {
    keys = Object.keys(M);
  } else {
    keys = markets;
  }
  const k2: number = keys;
  for (const m of [...keys].sort()) {
    const z: number = m;
  }
  let one = [];
  one = [1, 2];
  const o: string = one;
  let other = [];
  other = 'x' as any;
  const p: string = other;
}
