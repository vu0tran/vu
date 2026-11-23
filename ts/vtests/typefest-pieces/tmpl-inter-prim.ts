type A = `.${number}` & number;
const a: string = null as unknown as A;
type B = `.${number}` & string;
const b: number = null as unknown as B;
type C = `a${string}` & undefined;
const c: number = null as unknown as C;
type D<T> = `x${T & string}`;
const d: number = null as unknown as D<'y' | 3>;
export {};
