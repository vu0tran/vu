async function g() {
  const { make, k } = await import("mm");
  const a: string = make("x");
  const b: number = k;
  const m = await import("mm");
  const c: number = m.default;
  const n = await import("nn");
  const d: string = n.v;
  const e: number = n.default(1);
}
export {};
