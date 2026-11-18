export class A {
  #n: number | undefined = 1;
  #s = 'x';
  static #count = 0;
  #m(x: number) { return x + 1; }
  get v() { return this.#n; }
  f(o: A) {
    const a: string = this.#n;
    this.#n = 'q';
    const b: number = this.#m(2);
    A.#count++;
    if (this.#n !== undefined) { const c: number = this.#n; }
    const d: number = o.#s;
    return this.#zz;
  }
}
class B { #n = 1; }
export const ab: A = new B();
const fn = () => { class C { #p = 1; g() { return [1].map(() => this.#p); } } return C; };
export const r: number = fn();
