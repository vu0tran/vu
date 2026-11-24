import type { CatName, EvData, EvName, Obs } from './b';

type R = Record<string, unknown>;
export const t1 = (x: EvData<CatName, EvName<CatName>>) => x as R;
export const t2 = (x: Parameters<Obs['track']>[2]) => x as R;
export const t3 = (x: EvData<'sales', 'viewed'>) => x as R;
type G = <C extends 'a' | 'b', E extends C | 'z'>(c: C, e: E) => void;
export const t4 = (x: Parameters<G>[1]) => x as 'a';
type H = <C extends CatName, E extends EvName<C>>(c: C, e: E) => void;
export const t5 = (x: Parameters<H>[1]) => x as 'viewed';
type K = <C extends CatName, E extends EvName<C>>(d: EvData<C, E>) => void;
export const t6 = (x: Parameters<K>[0]) => x as R;
