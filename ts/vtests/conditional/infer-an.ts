// infer in conditional types outside generic aliases, from methods and generic signatures, and recursive aliases
export {};
type A = Awaited<Promise<void>>;
const a: A = 1;
type B = Awaited<Promise<string>>;
const b: B = 1;
type C = Awaited<Promise<Promise<number>>>;
const c2: C = 's';
type F1 = Promise<string> extends object & { then(onfulfilled: infer F, ...args: infer _): any } ? F : 0;
const f1: F1 = 1;
