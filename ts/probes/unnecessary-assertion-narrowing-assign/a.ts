// An assertion assigned to a variable of a union type: not reported as contextually unnecessary
// when it changes what the assignment narrows the variable to (isInNarrowingAssignment).
type A = { kind: 'a'; a: number };
type B = { kind: 'b'; b: string };
declare const wide: A | B;
declare const s: string;
declare const c: boolean;
export function f() {
  let v: A | B | undefined;
  v = wide as A;
  v = (wide as A);
  v = c ? (wide as A) : wide;
  v = wide as A | B;
  let w: string | number = 1;
  w = s as string;
  w = (s as 'x');
  let x: A | undefined;
  x = wide as A;
  let y: string | null | undefined;
  y = (s as string | undefined) ?? 'z';
  return [v, w, x, y];
}
