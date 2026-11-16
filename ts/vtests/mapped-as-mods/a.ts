// A key-remapping mapped type keeps the source property's modifiers (looked up by the key, not
// by the new name).
interface B { A?: (n: number) => void; C?: (n: string) => void; readonly D: number }
type E = { [K in keyof B as `${K}:exit`]: B[K] };
export const e: E = { "D:exit": 1 };
type R = B & Record<string, ((n: never) => void) | undefined> & E;
export const r: R = { D: 1, "D:exit": 2 };
declare const ee: E;
ee["D:exit"] = 3;
export const bad: E = {};
