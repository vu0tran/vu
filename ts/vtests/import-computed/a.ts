declare const p: string;
async function f() {
  const m = await import(p);
  const n: number = m.x;
  const q = import(p + "/a");
  const r: number = q;
  await import(p, { with: { type: "json" } });
}
export {};
