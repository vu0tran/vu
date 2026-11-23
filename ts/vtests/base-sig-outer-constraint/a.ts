// Inferring from a generic method of an instantiated class (getBaseSignature): its type parameter
// at its constraint instantiated with the class's type arguments, K extends keyof M at keyof F.
declare class Store<M> {
  get<K extends keyof M>(name: K): M[K];
}
type Fn = (...args: any[]) => any;
type Ret<T> = T extends (...args: any[]) => infer R ? R : never;
declare function fn<T extends Fn>(): { m: Ret<T> };
type F = { a: number; b: number };
type W = { m: Ret<Store<F>['get']> };
const w: W = fn();
const r: boolean = fn<Store<F>['get']>().m;
