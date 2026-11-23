// a spread of any, a readonly array or another iterable into an evolving array: any, the elements
declare const anyv: any;
declare const set: Set<number>;
declare const ro: readonly string[];
export function walk(d: string) {
  const out = [];
  out.push(...anyv);
  const n1: number = out;
  const out2 = [];
  out2.push(...set);
  out2.push(...ro);
  const n2: number = out2;
  return out;
}
