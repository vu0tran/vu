import type * as gql from '@gql';
declare const r: { kind?: gql.Kind };
export const a1 = r.kind as gql.KindStruct | undefined;
export const a2 = r?.kind as gql.KindStruct | undefined;
declare const e: gql.Kind;
export const a3 = e as gql.Other;
declare const n: number;
export const a4 = n as gql.Other;
