// The polymorphic this type: a class's this, members returning this seen from the receiver,
// and relating to an interface whose methods return this
interface Pausable { pause(): this; other(o: this): number; v: number }
class A {
  x = 1;
  v = 2;
  y?: string;
  pause(): this { return this; }
  other(o: this): number { return o.v; }
  m() { const n: number = this.x; if (this.y) { const s: string = this.y; } this.x = 2; return this; }
  p() { const z: A = this; const w: number = this; take(this); }
}
function take(a: A) {}
const q: A = new A().m();
const pz: Pausable = new A();
const f1: () => A = new A().pause;
declare const pp: Pausable;
const f2: () => number = pp.pause;
type P = Pick<Pausable, 'pause'>;
const pk: P = new A();
