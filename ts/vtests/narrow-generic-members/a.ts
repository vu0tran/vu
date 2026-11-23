// Narrowing references whose types have type parameters in them.
// typeof x === "boolean" on a type parameter: T & boolean
export function f<T>(x: T, o: { v: T }) {
  if (typeof x === 'boolean') { const z: number = x; }
  if (typeof o.v === 'boolean' && typeof x === 'boolean') { const z: number = o.v; }
}
export function k<T extends boolean>(x: T) {
  if (typeof x === 'boolean') { const z: number = x; } else { const w: number = x; }
}
export function countByValue<T>(xs: { count: number; value: T }[]) {
  return xs.sort((left, right) => {
    if (typeof left.value === 'number' && typeof right.value === 'number') return left.value - right.value;
    if (typeof left.value === 'boolean' && typeof right.value === 'boolean') return Number(right.value) - Number(left.value);
    return String(left.value).localeCompare(String(right.value));
  });
}
// === undefined / null on a conditional type or keyof
type Shape<D> = D extends { a: infer X } ? { x: X } : { y: D };
declare function mk<D>(d: D, i?: Shape<D>): number;
export const create = <Desc extends object>(schema: Desc, init?: Shape<Desc>): number => {
  if (init === undefined || init === null) {
    const u: number = init;
    return mk(schema, init);
  }
  const n: string = init;
  return 1;
};
export function kk<O>(key: keyof O | undefined) {
  if (key !== undefined) { const n: boolean = key; } else { const m: boolean = key; }
}
// a predicate's generic type on a type parameter
function isProperty<R extends { __typename: string }>(r: R): r is Extract<R, { __typename: 'Property' }> {
  return r.__typename === 'Property';
}
export function requireProperty<R extends { __typename: string }>(r: R | null | undefined): Extract<R, { __typename: 'Property' }> {
  if (!r || !isProperty(r)) {
    throw new Error(`Expected a Property result, got ${r?.__typename ?? 'null'}`);
  }
  const n: number = r;
  return r;
}
// 'name' in x where x is an intersection with a type parameter
type AnyFn = (...a: any[]) => any;
interface Mock<T extends AnyFn> { mockReturnValue(v: ReturnType<T>): void }
declare function mocked<T extends AnyFn>(v: T): Mock<T> & T;
export const m2 = <T extends AnyFn>(value: T) => {
  const mock = mocked(value);
  if ('extra' in mock) {
    const y: number = mock;
    return mock;
  }
  const z: number = mock;
  return mock;
};
// === a literal on Awaited<T>: kept either way
export async function direct<T>(perform: () => Promise<T>): Promise<T> {
  const result = await perform();
  if (result === false) { const n: number = result; }
  else { const m: number = result; }
  return result;
}
