// an unresolved name prints as written inside other types (Foo[], Pick<Foo, "x">); a member or call of it is plain
import { Foo, Bar } from './missing';
import * as gql from './missing2';
declare const a: Foo[];
declare const b: Pick<Foo, 'x'>;
declare const c: Foo | null;
declare const d: Promise<Foo>;
declare const e: (x: Foo) => Bar;
declare const f: gql.Maybe<gql.Baz>;
declare const g: Foo;
type L = Foo;
declare const h: L[];
declare const i: { k: Foo };
export const x1: number = a; export const x2: number = b; export const x3: number = c; export const x4: number = d;
export const x5: number = e; export const x6: number = f; export const x7: number = g; export const x8: number = h; export const x9: number = i;
declare const ds: Foo;
export const y1: null = [ds.get()];
