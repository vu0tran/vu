class A { x = 1; m() { return 2; } }
const p = A.prototype;
const n1: string = p;
declare abstract class B<T> { y: T; abstract z(): void }
const q = B.prototype;
const n2: string = q;
const r = B.prototype.z;
const n3: string = r;
declare class C { static prototype: number }
const n4: string = C.prototype;
const r2 = A.prototype.m;
const n5: string = r2();
A.prototype.x = 3;
