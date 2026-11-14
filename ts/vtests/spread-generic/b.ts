interface Arb<T> { v: T }
declare function constantFrom<T = never>(...values: T[]): Arb<T>;
declare function constantFrom<TArgs extends any[] | [any]>(...values: TArgs): Arb<TArgs[number]>;
const a = constantFrom<(k: string) => string>((k) => k, (k) => k + "1");
const b: number = a;
const c = constantFrom<number>(1, "x");
export {};
