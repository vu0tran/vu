type FV = Record<string, any>;
interface D extends FV { a?: string }
type PVI<T, P extends string> = T extends any ? P extends `${infer K}.${infer R}` ? K extends keyof T ? undefined extends T[K] ? PVI<T[K], R> | undefined : PVI<T[K], R> : never : P extends keyof T ? T[P] : never : never;
type Path<T> = keyof T & string;
export function f<N extends string>(x: PVI<D, N>) { const y: PVI<FV, N> = x; }
export const n: number = 'x';
