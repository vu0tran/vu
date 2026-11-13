declare function hasKey<T extends PropertyKey>(value: unknown, key: T): value is Record<T, unknown>;
function f() {
  const x: unknown = { a: 3 };
  if (hasKey(x, '0')) { const y: typeof x = 1; }
  const s: string | number = Math.random() ? "a" : 1;
  if (typeof s === "string") { const z: typeof s = 1; }
}
export {};
