// a generic mapped type narrowed by ?. and made non-nullable by ??
type DeepPartial<T> = { [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K] };
interface P<T extends string> {
  dis?: Partial<Record<T, string>>;
}
export function f<T extends string>({ dis }: P<T>, over?: DeepPartial<{ a: T }>) {
  const s: number = dis;
  const l = dis?.toString();
  const o = over ?? {};
  const q: number = o;
  return l;
}
