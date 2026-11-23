// C.prototype: the instance type, any for the class's type parameters (not Function's any)
declare class K<T = 1> { x: T; m(): string; }
class L { y = 1; }
K.prototype.nonexistent;
const a: string = K.prototype.x;
const b: number = K.prototype.m;
const c: string = L.prototype.y;
L.prototype = new L();
