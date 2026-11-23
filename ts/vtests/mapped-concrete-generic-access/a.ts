// { [K in keyof D]?: C<D[K]> }[T], T extends keyof D: its constraint is the template with T for K
// and undefined (substituteIndexedMappedType, isMappedTypeGenericIndexedAccess), also once every
// property of the mapped type has been typed (here by the initializer's check); not related to a
// target that neither it nor the mapped type indexed by T's constraint relates to
export {};
interface Detail { readonly a: number | null; readonly b: string | null; readonly c: boolean }
type Comp<T> = ((p: { value: T }) => void) & { parse: (raw: string) => T | undefined };
declare const numComp: Comp<number | null>;
declare const strComp: Comp<string | null>;
const COMPS: { [K in keyof Detail]?: Comp<Detail[K]> } = { a: numComp, b: strComp };
declare function use<T extends keyof Detail>(k: T, c: Comp<Detail[T]> | undefined): void;
function f<T extends keyof Detail>(k: T) {
  const c = COMPS[k];
  use(k, c);
  const d: Comp<Detail[T]> | undefined = COMPS[k];
  const e: Comp<Detail[T]> = COMPS[k];
  const g: number = COMPS[k];
  if (c) {
    const h: Comp<Detail[T]> = c;
    const v: Detail[T] | undefined = c.parse("x");
  }
}
type D = { a: number; b: string };
const M: { [K in keyof D]?: [D[K]] } = { a: [1], b: ["s"] };
function t<T extends keyof D>(k: T) {
  const z: string = M[k];
  const c = M[k];
  const y: [D[T]] = c;
  const x: [D[T]] | undefined = M[k];
}
