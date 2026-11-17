export {};
declare function ser(): { name?: string } | undefined;
export function f(c: Record<string, number>) {
  while (true) {
    const s = ser();
    if (!s) break;
    const q = s.name;
    if (q) { c[q] = 1; }
  }
}
