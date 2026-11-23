type Res = (x: unknown) => void;
interface DT<TI = unknown, TR = unknown, TN extends string = string, TRes extends Res = Res> { name: TN; input: (i: TI) => void; resolver: TRes; next?: (r: TR) => void }
type Call<TA = unknown, TN extends string = string, TRes extends Res = Res> = { id: string; name: TN; arguments: TA; resolver: TRes };
type ForTool<T> = T extends DT<infer TI, unknown, infer TN, infer TRes> ? Call<TI, TN, TRes> : never;
type U<T extends readonly DT[]> = ForTool<T[number]>;
export class H<const T extends readonly DT[]> {
  m = new Map<string, U<T>>();
  f(calls: U<T>[]) {
    for (const c of calls) { const n: number = c.id; this.m.set(c.id, c); }
  }
}
