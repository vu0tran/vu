// spreading arrays into object literals: Array's members, related to arrays
export {};
declare const arr: number[];
const r = { ...arr };
const a1: { [n: number]: number } = r;
const a2: { length: number } = r;
const a3: Pick<number[], "push" | "pop" | "concat" | "join" | "slice" | "sort" | "splice" | "map" | "filter" | "reduce"> = r;
const a4: Pick<number[], "every" | "some" | "forEach" | "indexOf" | "lastIndexOf" | "reduceRight" | "find" | "findIndex" | "fill" | "copyWithin"> = r;
const a5: Pick<number[], "entries" | "keys" | "values" | "includes" | "flatMap" | "flat" | "at" | "toString" | "toLocaleString" | "reverse" | "shift" | "unshift"> = r;
const a7: number[] = r;
