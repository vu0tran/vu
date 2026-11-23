// let x; ... x = []: an evolving array from there on.
declare const rules: [string, [string, string][]][];
export function closure() {
  const results: [string, unknown[]][] = [];
  rules.forEach(([g, css]) => {
    let prev;
    let cur;
    const groups: unknown[] = [];
    results.push([g, groups]);
    css.forEach(([cl, r]) => {
      if (prev !== cl) {
        if (cur) {
          groups.push([prev, cur]);
        }
        cur = [];
        prev = cl;
      }
      cur.push(r);
      const z: number = cur;
    });
    groups.push([prev, cur]);
    const y: number = cur;
  });
}
export function straight() {
  let x;
  x = [];
  x.push(1);
  x.push('a');
  const n: boolean = x;
  const len: string = x.length;
}
export function empty() {
  let y;
  y = [];
  const m: boolean = y;
}
export function inner() {
  let w;
  const f = () => {
    w = [];
    w.push(true);
    const k: string = w;
  };
  f();
}
export function plain() {
  let v;
  v = [1];
  v.push(2);
  const q: string = v;
}
declare const cond: boolean;
export function e1() {
  let x;
  if (cond) { x = []; x.push(1); } else { x = []; x.push('s'); }
  const n: boolean = x;
}
export function e2(xs: number[]) {
  let x;
  x = [];
  for (const v of xs) x.push(v);
  const n: boolean = x;
}
export function e3() {
  let x;
  x = [];
  x[0] = 'a';
  const n: boolean = x;
}
export function e4() {
  let x;
  x = [];
  x.push(1);
  x = 'str';
  const n: boolean = x;
}
export function e5() {
  let x;
  x = [];
  x.push(...[1, 2]);
  x.unshift(true);
  const n: boolean = x;
}
