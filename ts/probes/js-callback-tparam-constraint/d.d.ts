type Out<T> = T extends { _o: infer O } ? O : never;
export interface S<O> {
  _o: O;
  refine<Ch extends (arg: Out<this>) => unknown>(check: Ch): this;
  map<U, Ch extends (arg: O) => U>(check: Ch): S<U>;
}
export declare const s: S<string>;
