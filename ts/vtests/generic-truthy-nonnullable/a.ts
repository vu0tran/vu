export {};
interface B { describe(): number; upload?: (f: string) => void; frames?: () => string[] }
declare const options: { browser: B };
function capability<K extends keyof B>(name: K) {
  const method = options.browser[name];
  if (!method) throw new Error(`no ${name}`);
  return method;
}
const u: number = capability("upload");
const f: number = capability;
function other<K extends keyof B>(name: K) {
  const m = options.browser[name];
  if (m) return 1;
  const z: number = m;
  return 2;
}
function tp<T extends string | undefined>(x: T) {
  if (x) {
    const a: number = x;
    return x;
  }
  return 0;
}
const r: boolean = tp;
type C<T> = T extends string ? { s: T } | undefined : null;
function cd<T>(x: C<T>) {
  if (x) return x;
  return 1;
}
const q: boolean = cd;
