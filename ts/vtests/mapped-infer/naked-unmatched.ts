declare const xs: (string | number)[];
export const a: 'z' = xs.flatMap((x) => (typeof x === 'string' ? x : []));
declare function fm<U>(cb: () => U | ReadonlyArray<U>): U[];
export const b: 'z' = fm(() => (Math.random() ? 'a' : []));
declare const s1: string | never[];
export const c: 'z' = fm(() => s1);
