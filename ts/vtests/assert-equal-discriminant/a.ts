declare function strictEqual<T>(actual: unknown, expected: T, message?: string): asserts actual is T;
declare function isEq<T>(actual: unknown, expected: T): actual is T;
type R = { state: 'recorded'; receipt: { eventTime: string } } | { state: 'conflict' };
declare function lifecycle(x: number): Promise<R>;
export async function f() {
  for (const [a] of [[1], [2]]) {
    const first = await lifecycle(a);
    strictEqual(first.state, 'recorded');
    const z: number = first.receipt.eventTime;
  }
  const second = await lifecycle(1);
  strictEqual(second.state, 'recorded');
  const y: number = second.receipt.eventTime;
  const s: number = second.state;
  const v = isEq(1, 'a');
  const t: number = v;
}
