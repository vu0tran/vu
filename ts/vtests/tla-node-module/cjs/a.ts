// top-level await under module node20: allowed in an ES module file (type: module), TS1309 in a CommonJS one
declare function f(): Promise<number>;
export const x: string = await f();
