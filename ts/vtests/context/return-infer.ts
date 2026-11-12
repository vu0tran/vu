type P = { category: "a" | "b"; n: number };
declare const src: number[];
export const p1: P[] = src.map((n) => ({ category: "a", n }));
export const p2: readonly P[] = src.map((n) => ({ category: "a", n }));
declare function id<U>(f: () => U): U[];
export const p3: readonly P[] = id(() => ({ category: "a", n: 1 }));
export const p4: Iterable<P> = id(() => ({ category: "a", n: 1 }));
export const p5: ArrayLike<P> = id(() => ({ category: "a", n: 1 }));
