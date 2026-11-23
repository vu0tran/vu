type A = { __typename: 'A'; a: number };
type B = { __typename: 'B'; b: string };
declare const x: A | B | undefined;
export function f() {
  switch (x?.['__typename']) {
    case 'A': return x.a;
    case 'B': return x.b;
  }
  return 0;
}
export function g() {
  switch (x?.__typename) {
    case 'A': return x.a;
  }
  return 0;
}
export function h() {
  if (x?.['__typename'] === 'A') return x.a;
  return 0;
}
declare const y: A | B;
export function k() {
  switch (y['__typename']) {
    case 'A': return y.a;
  }
  return 0;
}
export function m() {
  switch (x?.['__typename']) {
    case 'A': { const n: string = x.a; return n; }
  }
  if (y['__typename'] !== 'A') { const s: number = y.b; return s; }
  return 0;
}
