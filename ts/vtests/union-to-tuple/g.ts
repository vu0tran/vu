declare const f: (x: "a") => 0;
const x: number = f;
declare const g: ((x: "a") => 0) & ((x: "b") => 0);
const y: number = g;
export {};
