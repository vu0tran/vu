interface Msg { headers: Record<string, string>; url?: string; }
interface Ctx<Q = { a?: string }, D = string> {
  req: Msg & { cookies: Partial<{ [k: string]: string }> };
  query: Q;
  d?: D;
}
type CSR = Omit<Ctx['req'], 'cookies'>;
export type CSC<Q = { a?: string }, D = string> = Omit<Ctx<Q, D>, 'req'> & { req: CSR };
export const mk = (headers: Record<string, string>) => ({ headers } as CSC['req']);
declare const e: unknown;
const a1: number = e as CSC['req'];
const a2: number = e as CSR;
