export {};
declare const p1: Partial<boolean>;
declare const p2: Partial<string | { a: 1 }>;
declare const p3: Readonly<number[] | string>;
function f<T>(t: Partial<T>) { return t; }
const b1: boolean = f<string | { a: 1 }>(null!);
const b2: string = p1;
const b3: boolean = p2;
const b4: boolean = p3;
