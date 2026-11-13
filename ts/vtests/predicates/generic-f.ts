export {};
declare function is<T>(v: unknown, t: T): v is T;
declare function isArr<T>(v: T | T[]): v is T[];
class A { a = 1 } class B { b = 2 }
declare function inst<T>(v: unknown, c: new () => T): v is T;
function f(u: unknown, w: string | string[], ab: A | B) {
	if (is(u, { a: 1 })) { const n: string = u; } else { const m: string = u; }
	if (isArr(w)) { const n: number = w; } else { const m: number = w; }
	if (inst(ab, A)) { const n: number = ab; } else { const m: number = ab; }
}
