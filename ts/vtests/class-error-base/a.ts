import { Store } from 'nope-missing';
export class S extends Store { static q = 1; }
new S(1, 2);
S.q;
S.zz;
const u: null = new S();
class U extends Store { constructor() { super(1, (e) => e); super.x(); this.y; } }
class V<X> extends Store { constructor(public x: X) { super({ f: (e) => e }); } m() { return this.x; } }
const v: null = new V(1).m();
const w: Store = 1;
function f(s: S) { s.zz; const z: null = s; }
class W extends Store { a = this.b; }
