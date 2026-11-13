declare function h<T>(x: { [P in keyof T]: T[P] }): T;
export const a: 'z' = h((s: number) => s);
