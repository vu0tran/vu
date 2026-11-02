// A few of oxlint's default rules, for the release smoke test.
export function check(x: number, s: string): boolean {
  debugger;
  const unused = 1;
  if (x == NaN) return false;
  if (typeof s === "strnig") return false;
  return /\-a/.test(s);
}
