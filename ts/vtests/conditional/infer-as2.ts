export {};
type F = () => number;
const r: ReturnType<F> = 's';
type MyRT<T> = T extends (...args: any) => infer R ? R : any;
const r2: MyRT<F> = 's';
type MyRT2<T> = T extends () => infer R ? R : any;
const r3: MyRT2<F> = 's';
type D = F extends (...args: any) => infer R ? R : 0;
const r4: D = 's';
