export {};
const docs = { a: { d: "x", e: 1 }, b: { d: "y" } };
const m = {
  z: 1,
  a: { ...docs.a, example: false },
  b: { ...docs.b, d: "w", example: "c" },
  c: { q: 1, ...docs.a },
} as const;
m.a.d = "q";
m.b.example = "x";
const o2 = { x: 1, ...{ x: 2 } } as const;
interface I { k?: number; j: string }
declare const ii: I;
const o3 = { ...ii, l: 1 } as const;
