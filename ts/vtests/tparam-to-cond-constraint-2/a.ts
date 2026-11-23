// a type parameter to a conditional type (with infer): through its constraint, the same instantiation
type CallOptions = { t?: number };
type Client = { [k: string]: (req: any, o?: CallOptions) => unknown };
type ExtractRequestType<T> = T extends (req: infer R, options?: CallOptions) => unknown ? R : never;
function invoke<C extends Client, M extends keyof C, TRequest extends ExtractRequestType<C[M]> = ExtractRequestType<C[M]>>(client: C, m: M, request: TRequest): void {}
export function make<C extends Client, M extends keyof C & string, TIn, TRequest extends ExtractRequestType<C[M]> = ExtractRequestType<C[M]>>(client: C, m: M, tr: (i: TIn) => TRequest, input: TIn): void {
  const p = tr(input);
  invoke(client, m, p);
  const s: string = 1;
}
export function g<C extends Record<string, () => unknown>, M extends keyof C>(r: ReturnType<C[M]>) {
  if (!(r instanceof Promise)) throw 1;
  const s: string = 2;
}
