export {};
const a1 = new A();
const a2 = () => new A();
type T = typeof A;
class B { x = new A(); static y = new A(); m() { return A; } }
const e1 = E.x;
function f() { return E.x; }
namespace N { export const q = new A(); }
if (true) { const z = new A(); }
const obj = { k: new A(), get g() { return new A(); } };
class A { static p = "a"; static self = new A(); }
enum E { x = 1 }
const enum CE { y = 2 }
const ce = CE.y;
let v = class { static s = new A(); };
