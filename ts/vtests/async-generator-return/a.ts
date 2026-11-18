export async function* g1(): AsyncGenerator<number, string, unknown> {
  yield 1;
  yield Promise.resolve(2);
  yield 'x';
  const v = yield 3;
  return 'done';
}
export async function* g2(): AsyncIterable<string> {
  yield 'a';
  yield 5;
}
export async function* g3(): AsyncIterableIterator<number> {
  yield 1;
  return;
}
export const g4 = async function* (): AsyncGenerator<number, number> {
  yield 1;
  return Promise.resolve(2);
};
export async function* g5(): AsyncGenerator<number, string> {
  return 3;
}
