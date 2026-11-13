declare function omit<T extends object, K extends keyof T>(obj: T, ...keys: K[]): Omit<T, K>;
type J = { a?: string; b?: number };
declare function use(j: J | boolean): number;
export const r: 'z' = use(omit({ a: 'x', n: true as const }, 'n'));
declare function pk<T, K extends keyof T>(o: T, k: K): Pick<T, Exclude<keyof T, K>>;
export const q: { a: number } = pk({ a: 1, b: '' }, 'b');
