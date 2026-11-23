// calling a union whose members' generic overloads match only in part (a default differs): the
// first member's overloads matched in every member (findMatchingSignatures), pg's Pool | PoolClient
interface R<T> { rows: T[]; n: number | null }
interface A {
  q<T = any, I = any[]>(text: string, values?: I): Promise<R<T>>;
  q<T = any, I = any[]>(cfg: { text: string; v?: I }): Promise<R<T>>;
  q<T = any, I = any[]>(cfg: { text: string; v?: I }, cb: () => void): void;
}
interface B {
  q<T = any, I = any>(text: string, values?: I): Promise<R<T>>;
  q<T = any, I = any[]>(cfg: { text: string; v?: I }): Promise<R<T>>;
  q<T = any, I = any[]>(cfg: { text: string; v?: I }, cb: () => void): void;
}
declare const x: A | B;
export async function f() {
  const r2 = await x.q<{ k: number }>({ text: 's' });
  const b: string = r2.rows[0].k;
  const v: number = x.q({ text: 's' }, () => {});
  return [b, v];
}
