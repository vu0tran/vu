// inference from a contextual type into a recursive conditional type stops once both the source
// and the conditional recur (invokeOnce's deeply nested check)
type Field<T, X, M extends 'P' | 'K' = 'P'> =
  Extract<T, object> extends never ? Prim<T, X, M> : Prim<Exclude<T, object>, X, M> | Obj<Extract<T, object>, X, M>;
type Prim<T, X, M extends 'P' | 'K'> = Extract<T, string> extends never ? undefined : Narrow<Extract<T, string>, X, M>;
type Obj<T, X, M extends 'P' | 'K'> = Extract<T, unknown[]> extends never ? Narrow<T, X, M> : Narrow<Exclude<T, unknown[]>, X, M> | Narrow<Extract<T, unknown[]>, X, M>;
type Narrow<T, X, M extends 'P' | 'K'> =
  M extends 'K' ? (X extends keyof T ? T[X] : undefined)
  : X extends `${infer L}.${infer R}` ? Field<Field<T, L, 'K'>, R>
  : X extends `${infer L}[${infer K}]${infer R}` ? Field<Field<Field<T, L>, K, 'K'>, R>
  : Field<T, X, 'K'>;
interface TD { a: number }
interface R { resultData: { runData: { [k: string]: TD[] } }; x?: string }
declare function get<O, P extends string, D = Field<O, P>>(data: O, path: P, d: D): Exclude<Field<O, P>, null | undefined> | D;
declare function get(object: any, path: string[], d?: any): any;
export function f(r: R, nodeName: string) {
  const q: [boolean] = [get(r, ['resultData', 'runData', nodeName, 'a'], null)];
  const q2: [boolean] = [get(r, 'resultData.runData', null)];
  return q;
}
