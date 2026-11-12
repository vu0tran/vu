declare function mk<T>(cb: (r: (v: T) => void) => void): Box<T>;
interface Box<T> { v: T }
export const p1: Promise<void> = new Promise((resolve) => { resolve(); });
export const p2: Box<void> = mk((r) => { r(); });
export function p3(): Box<void> { return mk((r) => { r(); }); }
export function p4(): Promise<void> { return new Promise((r) => { r(); }); }
declare class K<T> { constructor(cb: (r: (v: T) => void) => void); v: T }
export const p5: K<void> = new K((r) => { r(); });
