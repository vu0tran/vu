// Properties named by enum members ([E.A]) are late-bound: keyof gives the enum literals, and a
// union of all an enum's members prints as the enum.
declare enum E1 { A = 0, B = 40 }
interface B { [E1.A]: '+'; [E1.B]: '-' }
declare const k: keyof B;
export const o3: boolean = k;
declare const b: B;
export const o5: boolean = b[E1.A];
export const o6: boolean = b[0];
declare const v: B[keyof B];
export const o2: boolean = v;
const K = "kk";
interface D { [K]: 1; z: 3 }
declare const kd: keyof D;
export const o7: boolean = kd;
