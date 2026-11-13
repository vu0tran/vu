class Base<T> { v!: T; get(): T { return this.v; } }
export const A = class Named { x = 1; m() { return this.x; } };
export const a: 'z' = new A();
export const b: 'z' = new (class { p = 'q'; })();
export const B = class extends Base<number> { trigger(n: number) { return this.get() + n; } };
export const bb: 'z' = new B().trigger(1);
export const ctor: 'z' = A;
const C2 = class { constructor(public k: string) {} };
export const c2: number = new C2('a').k;
interface Ctl { new (): { h(): void } }
export const T1 = class T1 { h() {} } as Ctl;
export const m = { S: class { constructor() { return; } } };
