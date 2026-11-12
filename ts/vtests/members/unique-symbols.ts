// const x: unique symbol, and class members named by unique symbols
export {};
const TAG: unique symbol = Symbol.for('x');
const TAG2 = Symbol('y');
export abstract class Node {
  get [TAG](): true { return true; }
  [TAG2]() { return 1; }
}
declare const n: Node;
const a: number = n[TAG];
const b: string = n[TAG2]();
