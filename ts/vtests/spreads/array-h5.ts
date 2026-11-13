// spreading arrays into object literals: Array's members, related to arrays
export {};
interface P { [key: string]: number }
declare const arr: P[];
const r = { __rl: true, ...arr };
const t1: Pick<P[], "entries" | "values" | "includes" | "at" | "toString" | "toLocaleString" | "reverse" | "shift" | "unshift" | "slice" | "join" | "indexOf" | "lastIndexOf" | "forEach" | "reduceRight" | "findIndex" | "fill" | "copyWithin" | "findLast" | "findLastIndex" | "toReversed" | "toSorted" | "toSpliced" | "with"> = r;
const t2: { [Symbol.iterator](): ArrayIterator<P> } = r;
const t3: { readonly [Symbol.unscopables]: any } = r;
