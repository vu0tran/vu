// String mapping types of string: Uppercase<string> fits the strings it leaves unchanged
export {};
type U = Uppercase<string>;
const u1: U = 'ABC';
const u2: U = 'aBC';
declare const u3: U;
const s: string = u3;
const n: number = u3;
const u4: Lowercase<string> = u3;
const u5: `${string}` = u3;
