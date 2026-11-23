// A method with a computed name of a union of literals, or of number: an index signature of the
// method's type; the number index signature has only the number-like names' values.
declare const m: 'p' | 'q';
const o2 = {
  r: 1,
  [m]() { return 'x'; },
};
const t2: boolean = o2.p;
const t2b: boolean = o2.r;
declare const n: number;
const o3 = { [n]() { return 1; }, [`k${n}`]: 2 };
const t3: boolean = o3[0];
const t3b: boolean = o3.k;
const o4 = { [n]: 'a', [`k${n}`]: 2 };
const t4: boolean = o4[0];
