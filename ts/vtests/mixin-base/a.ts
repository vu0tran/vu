type Constructor<T> = new (...args: any[]) => T;
interface A1 { a(): number }
interface B1 { b: string }
declare class Base<T = string> { t: T; constructor(x: number) }
declare const CBase: Constructor<A1> & Constructor<B1> & typeof Base;
export declare class K extends CBase<boolean> { k: number }
declare const k: K;
export const r1: string = k.a();
export const r2: number = k.b;
export const r3: number = k.t;
declare const MBase: Constructor<A1> & Constructor<B1>;
export declare class M extends MBase { }
declare const m: M;
export const r4: string = m.a();
export const r5: number = m.b;
new K(1);
new K();
