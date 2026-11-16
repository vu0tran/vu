// A template literal type's span may be a conditional type, even inside an extends clause.
interface MSC {}
export type T4<Id> = Id extends `${MSC extends 1 ? 2 : 3}` ? 1 : string;
export type T6<Id> = Id extends `${infer R}${MSC extends Record<'suffix', infer S> ? S : 'b'}` ? R : 1;
export const q: T6<"xb"> = 2;
export type After = number;
export const z: After = "s";
