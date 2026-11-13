// computed property names of string or number type in object literals: index signatures
export {};
declare const k: string;
declare const n: number;
const f: { [x: string]: number[] } = { [k]: [1] };
const i: Record<string, { s: 1 }> = { [k]: { s: 1 } };
const d = { ["lit"]: 1, [1]: "o" }; const d1: string = d;
function g(): Record<string, number[]> { return { [k]: [1, 2], a: [] }; }
const m = { [k]: 1 };
