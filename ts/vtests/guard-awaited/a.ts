declare function isCancel(value: unknown): value is symbol;
declare function onCancel(): never;
export async function w1<T>(prompt: Promise<symbol | T>): Promise<T> {
  const result = await prompt;
  if (isCancel(result)) return onCancel();
  const z: number = result;
  return result;
}
export async function w2<T>(prompt: Promise<symbol | T>): Promise<T> {
  const result = await prompt;
  if (!isCancel(result)) { const z: number = result; return result; }
  const y: symbol = result;
  return onCancel();
}
interface M { a: A; b: B }
interface N0 { isKind<K extends keyof M>(k: K): this is M[K] }
interface A extends N0 { ka: 1 }
interface B extends N0 { kb: 1 }
interface C extends N0 { kc: 1 }
declare const x: A | B | C;
if (x.isKind('a')) { const t: number = x; }
