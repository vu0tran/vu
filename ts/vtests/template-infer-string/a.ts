export {};
interface N { version: number | string; name: string }
declare function f<T extends N>(n: T, v: `${T["version"]}`): T;
declare const s: string;
const r1 = f({ version: 1, name: "a" }, s);
const r1b: string = r1;
const r2 = f({ version: 2, name: "b" }, `${3 as number}`);
const r2b: string = r2;
declare function g<R extends string, O extends string, X extends string>(p: `${R}{${O}}${X}`): [R, O, X];
const g1: number = g(s);
declare function h<T extends string>(p: `${T}`): T;
const h1: number = h(s);
const h2: number = h("lit");
