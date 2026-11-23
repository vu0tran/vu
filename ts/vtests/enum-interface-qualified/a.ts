// A package's exported enum and an interface of its name beside it (sequelize's LOCK): E.A in the
// interface names the enum's member, the left name read with namespace meaning.
import { LOCK, Transaction } from "lk";

declare const t: Transaction;
export const a: number = t.LOCK.UPDATE;
export const b: LOCK.SHARE = t.LOCK.UPDATE;
export const c: LOCK.SHARE = LOCK.SHARE;
