type X = (string & {})[number];
const x: X = 1;
type Y = (string & { a: 1 })[number];
const y: Y = 1;
function f<T extends string & {}>(t: T) { const z: number = t[0]; }
export {};
