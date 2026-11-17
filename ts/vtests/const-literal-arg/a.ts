export {};
declare function oe<const T extends [string, ...string[]]>(values: T, def: T[number]): T;
const a = oe(["x", "y"], "x");
const a2: number = a;
