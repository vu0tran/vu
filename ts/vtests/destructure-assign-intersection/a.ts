// An object destructuring assignment from an intersection: its combined properties (a package's
// ({ payload } = await jwtVerify(...)), jose's JWTVerifyResult & ResolvedKey).
interface R<P> { payload: P; header: { alg: string } }
interface K { key: string }
declare function verify(t: string): Promise<R<{ sub: string }> & K>;
export async function f(t: string) {
  let payload: unknown;
  let key: string;
  ({ payload, key } = await verify(t));
  const n: number = payload;
  const m: number = key;
}
