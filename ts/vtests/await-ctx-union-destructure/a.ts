declare function continueTrace<V>(o: {}, cb: () => V): V;
declare function startSpan<T>(o: {}, cb: (s: number) => T): T;
declare function sendRequest(): Promise<string>;
async function f() {
  const h = await continueTrace({}, async () => await startSpan({}, sendRequest));
  const x: null = h;
}
async function g<T>(cb: (s: number) => Promise<T>): Promise<T> {
  return await startSpan({}, async (span) => { return await cb(span); });
}
type Item = ([{ t: 'a' }, number] & { x?: 1 }) | ([{ t: 'b' }, string] & { y?: 2 }) | [{ t: 'c' }, boolean];
declare const items: Item[];
for (const [h, it] of items) { const q: null = h; const r: null = it; }
async function k<V>(v: V): Promise<V> { const p: PromiseLike<Awaited<V>> = await v; return v; }
