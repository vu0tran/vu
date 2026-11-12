// instanceof a generic class narrows to it with any type arguments
export {};
class Box<T> { v!: T; get(): T { return this.v; } }
class Other { o = 1; }
declare const x: Box<number> | Other | string;
if (x instanceof Box) { const n: string = x; const g: string = x.get(); }
declare const u: unknown;
if (u instanceof Box) { const n: string = u; }
declare const o: object;
if (o instanceof Box) { const n: string = o; }
