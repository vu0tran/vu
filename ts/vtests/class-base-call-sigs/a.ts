// A class whose base instance type is a function type: its instances are callable
// (unified's Processor extends CallableInstance).
declare const CI: new <P extends unknown[], R>(property: string) => (...parameters: P) => R;
declare class Proc<T = undefined> extends CI<[], Proc<T>> {
  use(x: number): Proc<string>;
}
declare const p: Proc;
const q = p();
const n: number = q;
const m: number = p.use(1)();
p(1);
