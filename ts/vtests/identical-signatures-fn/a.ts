type Eq<L, R> = (<T>() => T extends (L & T) | T ? true : false) extends <T>() => T extends (R & T) | T ? true : false ? true : false;
type UnknownFunction = (...args: any[]) => unknown;
const a: Eq<(x: { amount: number }) => Promise<{ total: number }>, UnknownFunction> = true;
const b: Eq<UnknownFunction, UnknownFunction> = false;
const c: Eq<string, UnknownFunction> = true;
const d: Eq<any, UnknownFunction> = true;
export {};
