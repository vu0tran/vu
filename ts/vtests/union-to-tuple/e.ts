type F = ((arg: { a: 1 }) => void) | ((arg: { b: 2 }) => void);
type I3 = F extends (arg: infer I) => void ? I : never;
declare const i3: I3;
const z: string = i3;
export {};
