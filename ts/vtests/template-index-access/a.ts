// a template literal index type reads the template literal index signatures it is assignable to

declare const e2: { [x: `$${Lowercase<string>}`]: 1 };
declare const k2: `$${Lowercase<string>}`;
export const b2 = e2[k2];
export const c2: 2 = b2;
interface I { [x: `$${Lowercase<string>}`]: 1 }
export const c3: 2 = (null! as I)[k2];
type E1 = { [x: `$${Lowercase<string>}`]: 1 };
declare const e: E1;
declare const k: `$${Lowercase<string>}`;
export const a1: E1[`$${Lowercase<string>}`] = 1n;
export const b1 = e[k];
export const c1: 2 = b1;
