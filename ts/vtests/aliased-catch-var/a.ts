class SupErr extends Error { x = 1 }
declare function g(s: string): void;
export function h() {
  try { g("a"); } catch (error) {
    const superseded = error instanceof SupErr;
    if (superseded) {
      g(error.message);
    }
  }
  try { g("a"); } catch (error) {
    const superseded = error instanceof SupErr;
    if (superseded) {
      try { g("b"); } catch { g("x"); }
      g(error.message);
    }
  }
  try { g("a"); } catch (error) {
    if (error instanceof SupErr) {
      try { g("b"); } catch { g("x"); }
      g(error.message);
    }
  }
}
export function k() {
  try { g("a"); } catch (error) {
    const ok = error instanceof SupErr;
    if (ok) g(error.message);
    error = 1;
  }
  let v: unknown = 1;
  const isS = typeof v === "string";
  if (isS) g(v);
  let w: unknown = g;
  const isW = typeof w === "string";
  if (isW) g(w);
  w = 2;
}
