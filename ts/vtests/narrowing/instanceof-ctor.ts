export {};
interface Ctor<T> { new (d: number): T; init(x: T): void }
interface ZO { o: 1 } interface ZU { u: 1 }
declare const ZObj: Ctor<ZO>;
declare const ZUn: Ctor<ZU>;
function f(s: ZO | ZU | { z: 1 }) {
	if (s instanceof ZObj) { const b: boolean = s; }
	else if (s instanceof ZUn) { const b2: boolean = s; }
	else { const b3: boolean = s; }
}
