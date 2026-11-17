// An intersection source: this in its members' properties is the whole intersection; one
// member's private property keeps its declaration.
declare class E<T extends Record<keyof T, any[]> = {}> { on<K>(e: K, l: (...a: any[]) => void): this; private x; }
export interface M extends E { stdout: E | null }
declare const x: E & { stdout: E };
export const m2: M = x;
declare class F { on(): this; }
interface MF extends F { s: number }
declare const y: F & { s: number };
export const m3: MF = y;
