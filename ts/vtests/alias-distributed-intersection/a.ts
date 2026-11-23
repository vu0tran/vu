type EV<Map extends object> = Map[keyof Map];
type REV<Map extends object> = NonNullable<EV<Map>>;
type NN2<T> = NonNullable<T>;
type NN3<T> = T & {};
type IX<M> = NonNullable<M[keyof M]>;
type IX2<M> = M[keyof M] & {};
type W<M extends object> = {
  a(): REV<M>; b(): NN2<M[keyof M]>; c(): NonNullable<M[keyof M]>; d(): NN3<M[keyof M]>;
  e(): IX<M>; f(): IX2<M>; g(): NN2<EV<M>>; h(): NonNullable<EV<M>>;
};
declare function w<M extends object>(m: M): W<M>;
declare const m2: { [x: number]: 'A' | 'B' | null };
const x = w(m2);
export const y = { a: x.a(), b: x.b(), c: x.c(), d: x.d(), e: x.e(), f: x.f(), g: x.g(), h: x.h() };
export const z: { q: typeof y } = { q: y, r: 1 };
type T2<T> = { k(): NN2<T>; l(): NonNullable<T>; n(): NN3<T> };
declare function t2<T>(t: T): T2<T>;
const u = t2(m2[1]);
export const z2: { q: { k: ReturnType<typeof u.k>; l: ReturnType<typeof u.l>; n: ReturnType<typeof u.n> } } = { q: null!, r: 1 };
