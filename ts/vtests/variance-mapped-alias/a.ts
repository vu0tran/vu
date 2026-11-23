// Two instantiations of an alias of a mapped type over T[number]: by the alias's variance (its
// keys contravariant), before the generic mapped target rules; measured through a mapped type,
// so a failed check falls back to the structure (VarianceFlags.Unreliable)
type RFM<T extends readonly string[]> = { [K in T[number]]: string };
export function use<T extends string[] | string>(flags: T) {
  type TArray = T extends string[] ? T : [T];
  const y: RFM<readonly string[]> = {};
  const z: RFM<TArray> = y;
  const ab: RFM<["a", "b"]> = { a: "", b: "" };
  const a1: RFM<["a"]> = ab;
  const a2: RFM<["a"]> = { a: "" };
  const ab2: RFM<["a", "b"]> = a2;
  return z;
}
type Box<T> = { [K in "v"]: T };
declare const bs: Box<string>;
const bn: Box<number> = bs;
const bu: Box<string | number> = bs;
export {};
