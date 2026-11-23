for (const identity of [{ id: "p" }, { function: { name: "t" } }, {}]) {
  const a: number = identity.id ?? "";
  const b: number = identity.function?.name ?? "";
}
for (const x of [{ a: 1 }, { b: "s" }]) {
  const c: string = x.a ?? 0;
}
for (const n of [1, 2]) {
  const d: string = n;
}
export {};
