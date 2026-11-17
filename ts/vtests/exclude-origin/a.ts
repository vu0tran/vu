type GV = string | object | number | boolean | undefined | null;
interface IDO { [k: string]: GV }
declare class Buf { x: 1 }
type R = IDO | Buf | GV | GV[] | null;
declare function j(s: string): void;
export function f(x: Exclude<R, Buf>) { j(x); }
