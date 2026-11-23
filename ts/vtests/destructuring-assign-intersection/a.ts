// ({ a } = rhs) with rhs an intersection of object types: each name the intersection of the
// members' properties
interface R<P> { payload: P; protectedHeader: { alg: string } }
interface K { key: string; extra?: number }
declare function verify(t: string): Promise<R<{ sub: string }> & K>;
export async function f(t: string) {
  let payload: unknown;
  let key: string;
  let extra: number | undefined;
  ({ payload, key, extra } = await verify(t));
  const n: number = payload;
  const m: number = key;
  let wrong: number;
  ({ key: wrong } = await verify(t));
}
