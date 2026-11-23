type Cat<X extends unknown[], Y extends unknown[]> = [...X, ...Y];
const a: string = null as unknown as Cat<string[], number[]>;
const b: string = null as unknown as Cat<[1, ...string[]], [2, ...boolean[]]>;
const d: string = null as unknown as Cat<string[], [1, 2]>;
const e: string = null as unknown as Cat<[1?], number[]>;
export {};
