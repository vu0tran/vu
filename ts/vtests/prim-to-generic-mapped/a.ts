// A primitive to a generic mapped type: false where the keys aren't all the primitive's own or its properties there don't fit the template (structuredTypeRelatedTo's mapped target).
function f<T extends string>(n: number, s: string, k: T) {
  const a: Record<T, string> = n;
  const b: Record<T, string> = s;
  const c: Partial<Record<T, string>> = n;
  const d: { [P in T]?: string } = s;
  const e: { [P in T]?: "x" | 1 | null } = true;
}
function g<T extends "toFixed">(n: number) {
  const a: Record<T, string> = n;
  const b: Partial<Record<T, string>> = n;
}
