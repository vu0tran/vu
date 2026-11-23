type K = 'a' | 'b';
export function f1(k: K): string {
  switch (k) {
    case 'a':
      return 'x';
    case 'b':
      return 'y';
  }
}
export function f2(k: K): string {
  switch (k) {
    case 'a':
      return 'x';
    default:
      return 'y';
  }
}
enum E { A, B }
export function f3(e: E): number {
  switch (e) {
    case E.A:
      return 1;
    case E.B:
      return 2;
  }
}
export function f4(k: K): string {
  if (k === 'a') return 'x';
  switch (k) {
    case 'b':
      return 'y';
  }
}
export function f5(b: boolean): string {
  switch (b) {
    case true:
      return 'x';
    case false:
      return 'y';
  }
}
export function f6(k: K): string | undefined {
  switch (k) {
    case 'a':
      return 'x';
    case 'b':
      return;
  }
}
function fail(): never { throw new Error(); }
export function g1(k: K): string {
  if (k === 'a') return 'x';
  fail();
}
export function g2(k: K): string {
  if (k === 'a') return 'x';
  while (true) {}
}
export function g3(k: K): string {
  switch (k) {
    case 'a':
      return 'x';
    case 'b':
      return 'y';
    default:
      throw new Error();
  }
}
export function g4(k: K): string {
  switch (k) {
    case 'a':
      return 'x';
    case 'b':
      return 'y';
  }
  return 'z';
}
export const g5 = (k: K): string => {
  switch (k) {
    case 'a':
      return 'x';
    case 'b':
      return 'y';
  }
};
