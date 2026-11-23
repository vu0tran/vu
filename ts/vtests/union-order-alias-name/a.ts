type Flip = { id: string; n: number };
type Address = { street: string };
type Zed = { z: number };
interface Mid { m: string }
declare const x1: Flip | PromiseLike<Flip> | Error;
export const y1: number = x1;
declare const x2: Error | Address;
export const y2: number = x2;
declare const x3: Zed | Mid | { q: 1 } | Address;
export const y3: number = x3;
type G<T> = { g: T };
declare const x4: G<string> | Error | Address;
export const y4: number = x4;
