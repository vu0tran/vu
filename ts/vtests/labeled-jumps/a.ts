// labeled continue and break to an outer loop: that loop's back edge or exit
declare function g(): { cf?: Promise<void> };
declare function h(): string | number;
export function f(n: number) {
  let cf: Promise<void> | undefined;
  lp: while (n > 0) {
    for (let t = 0; t < 3; t++) {
      try {
        if (n) continue lp;
        cf = g().cf ?? cf;
      } catch (e) {}
    }
    n--;
  }
  const z: number = cf;
  let x: string | number | boolean = true;
  outer: for (let i = 0; i < n; i++) {
    for (const k of [1, 2]) {
      x = h();
      if (typeof x === 'string') break outer;
      if (k) continue outer;
      x = false;
    }
    const y: null = x;
  }
  const w: null = x;
}
