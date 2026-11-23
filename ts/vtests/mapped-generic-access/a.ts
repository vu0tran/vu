type Detail = { a: number | null; b: string | null; c: boolean | null; d: readonly string[] };
interface Edit<T> { parse: (raw: string) => T | undefined; onChange: (v: T) => void }
declare const EDIT: { [K in keyof Detail]?: Edit<Detail[K]> };
export function f<K extends keyof Detail>(prop: K, raw: string): Detail[K] | undefined {
  return EDIT[prop]?.parse(raw);
}
export function g<K extends keyof Detail>(prop: K, raw: string): number {
  return EDIT[prop]?.parse(raw);
}
declare const ALL: { [K in keyof Detail]: Edit<Detail[K]> };
export function h<K extends keyof Detail>(prop: K, v: Detail[K]) {
  ALL[prop].onChange(v);
  const p: (raw: string) => Detail[K] | undefined = ALL[prop].parse;
  const q: (raw: string) => string = ALL[prop].parse;
}
