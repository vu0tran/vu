// Inferring from a generic signature whose rest parameter is a tuple: its elements are parameters.
type BoundFunction<T> = T extends (container: HTMLElement, ...args: infer P) => infer R ? (...args: P) => R : never;
type QueryByText<T extends HTMLElement = HTMLElement> = (container: HTMLElement, id: string, options?: { a?: number }) => T | null;
declare function queryByText<T extends HTMLElement = HTMLElement>(...args: Parameters<QueryByText<T>>): ReturnType<QueryByText<T>>;
declare function plain(container: HTMLElement, id: string): number;
declare function gen<T extends HTMLElement = HTMLElement>(container: HTMLElement, id: string): T | null;
export const a: number = null as unknown as BoundFunction<typeof plain>;
export const b: number = null as unknown as BoundFunction<typeof gen>;
export const c: number = null as unknown as BoundFunction<typeof queryByText>;
