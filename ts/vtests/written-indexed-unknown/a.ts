// a written indexed access on unknown with a literal key (a let assigned in a try, returned, read
// through ReturnType): TS2339 and the error type
import { Client } from './missing';
declare const client: Client;
declare function call<T>(o: { run: () => Promise<T> }): Promise<T>;
export async function page() {
  let response;
  try {
    response = await call({ run: () => client.get({ a: 1 }) });
  } catch (error) {
    throw error;
  }
  if (response.rowCount < 0) throw new Error('x');
  return response;
}
type R = Awaited<ReturnType<typeof page>>['rows'][number];
declare const r: R;
const n: number = r;
const m: number = page;
export async function page2() {
  let v;
  try { v = await Promise.resolve({ rows: [1] }); } catch (e) { throw e; }
  return v;
}
const m2: number = page2;
