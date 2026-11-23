// the value of a yield in a generator without a return type: the contextual signature's
// Generator<Y, R, TNext>'s TNext (mobx-state-tree's flow), else any (TS7057 where it has no context)
declare function flow<R, Args extends any[]>(g: (...args: Args) => Generator<any, R, any>): (...args: Args) => Promise<R>;
declare function typed(g: () => Generator<number, void, string>): void;
declare function fetchIt(): Promise<{ id: number }>;
export const load = flow(function* load(x: number) {
  let got: { id: number };
  got = yield fetchIt();
  const v = yield x;
  return got.id + v;
});
typed(function* () {
  const s = yield 1;
  const n: number = s;
  void n;
});
export function* plain() {
  const w = yield 1;
  let z: string;
  z = yield 2;
  return [w, z];
}
