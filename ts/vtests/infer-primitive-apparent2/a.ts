// A primitive source infers through its apparent type (inferFromTypes' getApparentType):
// String is ArrayLike<string> and Iterable<string>.
declare const token: string;
declare function f1<T>(x: Iterable<T>): T[];
const a1: null = f1(token);
declare function f2<T>(x: ArrayLike<T>): T[];
const a2: null = f2(token);
declare function f3<T>(x: Iterable<T> | ArrayLike<T>): T[];
const a3: null = f3(token);
const a4: null = Array.from(token);
const a5: null = Array.from('abc');
declare function f4<T>(x: { length: T }): T;
const a6: null = f4('abc');
const a7: null = f4(1 as number);
export const ok = Array.from(token).some((char) => /\s/.test(char) || char.charCodeAt(0) < 32);
