// A class extending a constructor whose instances are functions (unified's CallableInstance):
// the class's instances are callable with the base's call signatures.
declare const CallableInstance: new <P extends unknown[], R>(property: string | symbol) => (...parameters: P) => R;
declare class Processor<T = undefined> extends CallableInstance<[], Processor<T>> {
  use(x: number): Processor<string>;
  data: T;
}
declare const unified: Processor;
const a = unified();
const b = unified().use(1)();
const n1: number = a;
const n2: number = b;
const n3: number = b.data;
const n4: number = unified.use(2)().use(3)().data;
export {};
