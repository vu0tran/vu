type A = (object & Record<string, number>)[string];
type B = (object & Record<symbol, boolean>)[symbol];
type C2<T extends object> = (T & Record<string, number>)[string];
const a: string = 1 as A;
const b: string = true as B;
const c: string = 1 as C2<{}>;
export {};
