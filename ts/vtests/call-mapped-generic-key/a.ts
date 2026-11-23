// a call of a mapped type's property by a generic key, Record<K, F>[K]: F's signatures
type SyncRun = { a: number };
declare const run: SyncRun;
export function f<K extends string>(picks: Record<K, (run: SyncRun) => number>, key: K) {
  const r: string = picks[key](run);
  picks[key]('x');
  const m: { [P in K]: (n: number) => P[] } = null!;
  const s: number = m[key](1);
  return r;
}
