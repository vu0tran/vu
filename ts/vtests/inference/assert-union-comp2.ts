function f<T extends {}, X extends { a?: 1 }>(x: T, y: X) {
  const a1 = x as { a: 1 } | { b: 1 };
  const a2 = x as { a: 1 } | null;
  const a3 = x as (() => void) | string;
  const a4 = x as string[] | number[];
  const b1 = y as string | number;
  const b2 = y as { b: 1 } | { c: 1 };
}
export {}
