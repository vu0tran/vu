type K = "a" | "b";
function f<T extends readonly K[]>(flags: T) {
  const x = [...flags];
  const y: string = x;
  const z = { keys: [...flags] };
  const w: number = z;
  const v = [1, ...flags];
  const u: number = v;
  const q = [...flags] as const;
  const r: number = q;
}
function g<const T extends readonly K[]>(o: { a: K[]; b: T }) {
  const x = [...o.a, ...o.b];
  const y: number = x;
}
