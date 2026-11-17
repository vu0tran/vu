// A generic class whose type parameter is in a conditional type: its members decide (private ones
// of one declaration too), a method's callback parameters bivariantly.
type CB = () => void | Promise<void>;
type W<OC> = OC extends null ? false : true;
type Ctx<C> = C extends null ? J : NonNullable<C>;
type Call<C, B extends boolean = false> = (this: Ctx<C>, onComplete: B extends true ? CB : never) => void | Promise<void>;
declare class J<OC extends CB | string | null = null, C = null> {
	private _a;
	onComplete?: W<OC> extends true ? CB : undefined;
	addCallback(callback: Call<C, W<OC>>): void;
}
declare const j: J<CB | string | null>;
export const k: J = j;
declare class K<OC> { private x: OC }
declare const k1: K<string | null>;
export const k2: K<null> = k1;
export declare class A { private a; b; protected c; }
export class B { private a; }
type P<OC> = { e: ((x: unknown) => void) | null; o: OC } & ({ tz?: string } | { off?: number });
declare class Q<OC extends CB | string | null = null> {
	private _b;
	onComplete?: W<OC> extends true ? CB : undefined;
	errorHandler?: P<OC>['e'];
	addCallback(callback: Call<null, W<OC>>): void;
	static from<OC extends CB | string | null = null>(p: P<OC>): Q<OC>;
}
declare const q1: Q<CB | string | null>;
export const q2: Q = q1;
