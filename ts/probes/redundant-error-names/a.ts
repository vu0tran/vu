// which error type keeps its unresolved name (a reference, an alias of one, an indexed access,
// typeof a variable declared with it) and which is plain any (an intersection, a union, a
// conditional type, typeof a variable typed by its initializer)
import { graphql, Named } from '@gql';
import type { Loan, Same, Picked, Both } from './b';
const Doc = graphql('q');
type ResultOf<T> = T extends { __r?: infer R } ? R : never;
type A1 = NonNullable<ResultOf<typeof Doc>['x']>;
type A2 = ResultOf<typeof Doc>;
type A3 = ResultOf<Named>;
type A4 = NonNullable<Named>;
type A5 = Named['x'];
type A6 = typeof Doc;
declare const n: Named;
const y = n.a;
type B1 = Named & { k: 1 };
type B2 = Named | { k: 1 };
type B3 = typeof n;
type B4 = typeof y;
export interface I { a1: A1 | null; a2: A2 | null; a3: A3 | null; a4: A4 | null; a5: A5 | null; a6: A6 | null; a7: Named | null }
export interface J { b1: B1 | null; b2: B2 | null; b3: B3 | null; b4: B4 | null; y: typeof y }
export interface K { l: Loan | null; s: Same | null; p: Picked | null; b: Both | null; q: Partial<Named> | null }
