type A = {}[never];
export const a: A = 1 as never;
export const b: 'z' = null! as { x: 1 }[never];
type K<T> = { [P in keyof T]: T[P] }[keyof T];
export const c: 'z' = null! as K<{}>;
