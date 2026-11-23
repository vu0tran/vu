// A for-of variable's type is widened as a declaration's is: the object literals of an array
// literal get the properties the others have, optional and undefined.
export function f() {
  for (const s of [{ a: 1, e: 2 }, { a: 2 }, { a: 3, r: 'x', e: 3 }]) {
    const n: string = s.r;
  }
  const arr = [{ a: 1 }, { a: 2, r: 'x' }];
  for (const t of arr) { const k: number = t.r; }
  for (const u of ['a', 'b']) { const v: number = u; }
}
