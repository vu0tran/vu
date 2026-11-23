// yield* in an async generator: an async iterable's elements, a sync iterable's awaited; the
// value: an AsyncGenerator's TReturn
export {};
async function* inner(): AsyncGenerator<number, string> { yield 1; return "done"; }
function* sync(): Generator<Promise<boolean>> { yield Promise.resolve(true); }
async function* outer() {
  const r = yield* inner();
  const s: number = r;
  yield* [1, 2];
}
async function* outer2() {
  yield* sync();
}
for await (const x of outer()) { const y: string = x; }
for await (const x of outer2()) { const y: string = x; }
