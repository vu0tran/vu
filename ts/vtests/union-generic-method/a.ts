type Input<S, I = any> = (S extends string ? string : never) | I | { id: S };
type Cfg<F extends Record<string, any> = Record<string, any>, X = any> = { f?: F } & { x?: X };
declare class Base<S = number, I = any> {
  invoke<T extends Input<S, I>, C extends Cfg | undefined>(input: T, config?: C): Promise<T>;
}
declare class A extends Base<string> {}
declare class B extends Base<boolean> {}
declare class D extends Base<boolean, string> {}
declare const t: A | B;
export const r: number = t.invoke('x');
