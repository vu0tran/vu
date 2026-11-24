type Msg<N extends string = string> = { readonly $typeName: N; $unknown?: unknown[] };
type MInit<T extends Msg> = T | {
  [P in keyof T as P extends '$unknown' ? never : P]?: P extends '$typeName' ? never : FInit<T[P]>;
};
type Sel<K extends string, M extends Msg> = { case: K; value: M };
type FInit<F> = F extends string | number | boolean
  ? F
  : F extends Msg
    ? MInit<F>
    : F extends Sel<infer C, infer V>
      ? { case: C; value: MInit<V> }
      : F;

export type Viewed = Msg<'ev.Viewed'> & {
  /**
   * @deprecated use leadUuid
   */
  leadKey: string;
  leadUuid: string;
};
export type Signed = Msg<'ev.Signed'> & {
  /** @deprecated gone */
  leadKey: string;
  offer: string;
};
export type Group = Msg<'ev.Group'> & {
  event: Sel<'viewed', Viewed> | Sel<'signed', Signed> | { case: undefined; value?: undefined };
};
export type Wrapper = Msg<'ev.Wrapper'> & {
  category: Sel<'sales', Group> | { case: undefined; value?: undefined };
};
type WInit = MInit<Wrapper>;
type CatU = NonNullable<WInit['category']>;
type CatC = Extract<CatU, { case: string }>;
export type CatName = CatC['case'];
type CatData<C extends CatName> = NonNullable<Extract<CatC, { case: C }>['value']>;
type CatEvents<C extends CatName> = NonNullable<CatData<C>['event']>;
export type EvName<C extends CatName = CatName> = NonNullable<CatEvents<C>['case']>;
type Ev<C extends CatName, E extends EvName<C>> = Extract<CatEvents<C>, { case: E }>;
export type EvData<C extends CatName, E extends EvName<C>> = Ev<C, E>['value'];

export interface Obs {
  track<C extends CatName, E extends EvName<C>>(c: C, e: E, d: EvData<C, E>): void;
}
declare const obs: Obs;
export function use(): Obs {
  return obs;
}
