type C1<T> = T extends string ? T : T;
export function k1<T>(a: C1<T>): T { return a; }
export function k4<T extends { a: 1 }>(a: Awaited<T>): T { return a; }
