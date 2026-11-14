type requiredKeys<T extends object> = { [k in keyof T]: undefined extends T[k] ? never : k }[keyof T];
type optionalKeys<T extends object> = { [k in keyof T]: undefined extends T[k] ? k : never }[keyof T];
type AQ<T extends object> = Pick<T, requiredKeys<T>> & Partial<Pick<T, optionalKeys<T>>>;
type X = AQ<{ a: number; b?: string }>;
const x: X = { a: 1 };
const y: X = { b: "s" };
function f<T extends object>(t: T, k: requiredKeys<T>): keyof T { return k; }
function h<T extends object>(k: { [k in keyof T]: string }[keyof T]): keyof T { return k; }
function m<T extends object>(k: { [k in keyof T]: k }[keyof T]): keyof T { return k; }
function n<T extends object>(k: { [k in keyof T]: T[k] }[keyof T]): T[keyof T] { return k; }
