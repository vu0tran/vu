type SI<T, R> = (value: T, index: number, s: string) => R;
type AI<T, R> = (value: T, index: number, a: T[]) => R;
declare function mv<R>(obj: string | null | undefined, cb: SI<string, R>): { [n: number]: R };
declare function mv<T, R>(arr: T[], cb: AI<T, R>): { [n: number]: R };
export const a: 'z' = mv([1], (v) => v + 1);
export const b: 'z' = mv("ab", (v) => v.length);
