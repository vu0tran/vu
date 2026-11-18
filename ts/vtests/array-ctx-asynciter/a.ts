type MF = { role: string; content: string } & Record<string, unknown>;
declare function take(m: MF | MF[] | string): void;
take([{ role: 'u', content: 'x' }]);
take([1]);
declare class Stream<T> {
  next(): Promise<IteratorResult<T>>;
  [Symbol.asyncIterator](): this;
}
declare const st: Stream<number>;
export async function f() {
  for await (const x of st) {
    const s: string = x;
  }
}
