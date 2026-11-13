function f<T extends {}, U, V extends object, W extends string>(x: T, u: U, v: V, w: W) {
  const a1 = x as string | number;
  const a2 = x as string | undefined;
  const a3 = x as "a" | "b";
  const a4 = x as number | boolean;
  const a5 = x as string | { a: 1 };
  const a6 = x as { a: 1 };
  const b1 = u as string | number;
  const b2 = u as string;
  const c1 = v as string | number;
  const c2 = v as { a: 1 } | string;
  const d1 = w as number | boolean;
  const d2 = w as "x" | number;
  const d3 = x as 1 | 2;
}
export {}
