// a union member that is an object literal lacking the property: undefined from it
interface C { long_name: string; types: string[] }
declare const xs: C[];
const v = (xs.find((x) => x.types.length > 0) || {}).long_name;
const n: string | undefined = v;
const w = (Math.random() ? { a: 1 } : { b: 's' }).a;
const m: number | undefined = w;
export {};
const z: number = 'x';
