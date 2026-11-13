export {};
interface A { [k: string]: string; foo(): void; bar: number; "a-b": 1; 3: string; }
interface B { [k: number]: string; 3: number; x: number; "4": boolean; }
interface C { [k: string]: number; readonly [k: number]: string; }
type D = { [k: string]: number; get g(): string; set s(v: boolean) };
class E { [k: string]: number; x = "s"; m() {} static y = "q"; #p = "z"; }
type G = { [k: string]: number | undefined; o?: number };
function f(a: { [k: string]: 1; x: 2 }): { [k: number]: 1; 0: 2 } { return null!; }
