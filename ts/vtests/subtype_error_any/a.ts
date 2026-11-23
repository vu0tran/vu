// chooseOverload's first pass uses the subtype relation: the error type (an any) is a subtype of
// any and unknown only, and an object with members isn't a subtype of a fresh empty object
// literal. reduce's (prev: T) overload doesn't fit the callback; the generic one infers U from
// the callback's return, not from {}.
import * as gql from './missing';
declare const members: Array<gql.Member>;
const byId = members.reduce(
  (map: { [key: string]: gql.Member }, member: gql.Member) => {
    map[member.id] = member;
    return map;
  },
  {},
);
export const n: number = byId;
declare function pick<U>(a: U, b: U): U;
declare const rec: { [k: string]: number };
export const m: number = pick(rec, {});
export const k: number = pick({}, rec);
