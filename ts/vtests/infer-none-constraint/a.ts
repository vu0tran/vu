// No inference and no default: the type parameter is its constraint (getInferredType), also when
// unknown would satisfy it (an error type, {} | null | undefined); a written any constraint is unknown.
import * as gql from './missing';
import { S, toT, fromT } from './missing2';

declare function f<T extends {} | null | undefined, U extends gql.Value, V extends any, W>(): [T, U, V, W];
export const r1: number = f();

const mk = <TPb extends { a: string }, TGql extends gql.Value, TIn>(
  klass: TPb[],
  to: (pb: TPb) => TGql,
  from: (input: TIn) => TPb,
) => ({ klass, to, from });
export const r2: number = mk(S, toT, fromT);

declare function g<T extends string = 'd'>(x?: T): T;
export const r3: number = g();
