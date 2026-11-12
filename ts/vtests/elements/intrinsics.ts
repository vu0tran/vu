// The lib's intrinsic aliases on literals: Uppercase, Lowercase, Capitalize, Uncapitalize, NoInfer
export {};
type A = Uppercase<'abc' | 'dEf'>;
const a: A = 'x';
type B = Capitalize<'hello'>;
const b: B = 'hello';
type C = Uncapitalize<'Hello'> | Lowercase<'ABC'>;
const c2: C = 'z';
const n: NoInfer<number> = 's';
