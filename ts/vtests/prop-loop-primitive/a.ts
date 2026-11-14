function f(input: string, ps: { regex: RegExp }[]) {
  for (const p of ps) {
    const { regex } = p;
    regex.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = regex.exec(input)) !== null) {
      if (m[0].length === 0) { regex.lastIndex++; continue; }
      const s: string = regex.lastIndex;
    }
    const t: string = regex.lastIndex;
  }
}
function g(o: { n: number; u: number | undefined; s: string }) {
  for (let i = 0; i < 3; i++) { o.n = i; o.u = undefined; o.s = "x"; }
  const a: string = o.n;
  const b: string = o.s;
  const c: number = o.u;
}
export {};
