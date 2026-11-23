// an array spread before the last element in a tuple context: a rest element followed by fixed
// ones ([...string[], "x"])
declare function e<const T extends readonly [string, ...string[]]>(v: T): T;
declare const xs: string[];
declare const ns: number[];
const a = e([...xs, 'x']);
const n1: number = a;
declare function t<T extends readonly unknown[]>(v: [...T]): T;
const b = t([...xs, 1, ...ns, true]);
const n2: number = b;
const c = t([1, ...xs, 'y']);
const n3: number = c;
