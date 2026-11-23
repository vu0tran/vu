// A generic whose base constraint is Record<string, any>'s any: indexed and related as any; a
// destructured default in an annotated parameter takes only undefined out of the type.
type FV = Record<string, any>;
type PV2<T, P> = T extends any ? P extends `${infer K}.${infer R}` ? (K extends keyof T ? PV2<T[K], R> : never) : P extends keyof T ? T[P] : never : never;
export function h<T extends FV, N extends string>(v: PV2<T, N>, k: string) {
  if (typeof v === 'object') { const x = v[k]; const y: number = x; }
  const z: { q: 1 } = v;
}
type RO<T> = { required?: string; [K: `x${string}`]: T };
export function d<T>({ validation = {} }: { validation?: Omit<RO<T>, 'min'> }) {
  if (!validation.required) validation.required = 'a';
  const n: number = validation;
}
