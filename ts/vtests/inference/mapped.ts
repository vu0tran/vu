// Inference to generic mapped types: reverse mapped types (Partial<T>, { [K in keyof T]: Box<T[K]> },
// a rest parameter of one) and { [P in K]: V } (K from the keys, V from the properties)
export {};
declare function part<T>(x: Partial<T>): T;
const a = part({ a: 1, b: 's' });
const na: number = a;
declare function ro<T>(x: Readonly<T>): T;
const b = ro({ x: true });
const nb: number = b;
interface Box<V> { v: V }
declare function unbox<T>(x: { [K in keyof T]: Box<T[K]> }): T;
const c1 = unbox({ p: { v: 1 }, q: { v: 'z' } });
const nc: number = c1;
declare function tup<Ts extends unknown[]>(...arbs: { [K in keyof Ts]: Box<Ts[K]> }): Ts;
const d = tup({ v: 1 }, { v: 's' });
const nd: number = d;
declare function rec<K extends string, V>(x: { [P in K]: V }): [K, V];
const e = rec({ a: 1, b: 2 });
const ne: number = e;
