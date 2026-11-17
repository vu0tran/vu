export {};
interface NI { readonly name: string; opt?: number; onError(h: NI): this }
const inst: NI = {
  name: "a",
  opt: 1,
  onError(h: NI) { return this; },
};
declare const other: NI;
const inst2: NI = {
  name: "a",
  opt: 1,
  onError(h: NI) { return other; },
};
