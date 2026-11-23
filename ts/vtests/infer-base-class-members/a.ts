// inferring a base class's type argument from a derived class's instance: identical members of
// an intersection target are matched by structure, instantiations of one alias in a union
declare class Base<E, S, B extends string = "/"> {
  get: <P extends string>(p: P) => Base<E, S & { [K in P]: 1 }, B>;
  route<SP extends string, SS>(path: SP, app: Base<any, SS, any>): Base<E, Merge<SS, SP> | S, B>;
  private _e?: E;
}
type Merge<O, P extends string> = { [K in keyof O as `${P}${K & string}`]: O[K] };
declare class Mid<E, S, B extends string = "/"> extends Base<E, S, B> {}
declare class Top<E, S, B extends string = "/"> extends Mid<E, S, B> {
  openapi(): Top<E, S, B>;
}
type C = Top<{ x: 1 }, { "/x": { a: 1 } }, "/">;
type S = C extends Base<any, infer S, any> ? keyof S : 0;
export const n: S = 1;
