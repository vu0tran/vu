type FV = { product: 'A' | 'B'; docs: string[] };
type Paths = 'product' | 'docs' | `docs.${number}`;
type PV<T, P> = P extends keyof T ? T[P] : never;
interface Cfg { dirty?: boolean }
function f<N extends Paths>(v: FV[N & keyof FV], w: PV<FV, N>) {
  const c: string | string[] = w;
  const d: string | string[] = v;
}
type Rec = { [k: string]: string | boolean | undefined };
type PV2<T, P> = P extends `${infer K}.${infer R}` ? K extends keyof T ? R extends keyof T[K] ? T[K][R] : never : never : never;
function g<N extends string>(w: PV2<Rec, N>) {
  const c: string | boolean | undefined = w;
}
export {};
const z: number = "s";
