interface NodeArr<T> extends ReadonlyArray<T> { readonly pos: number }
declare const na: NodeArr<string> | undefined;
const [items] = na ?? [];
const n1: number = items;
declare const col: "brand" | "error" | `x${string}`;
const [label, cls] = col;
const n2: number = label;
const n3: number = cls;
function each(f: (c: "a" | "b") => void) { f("a"); }
each(([l, k]) => { const z: number = l; const w: boolean = k; });
