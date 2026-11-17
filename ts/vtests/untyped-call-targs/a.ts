import { Bad } from "nope";
function f<T extends Bad>(qb: T): T { qb.andWhere(1); const x: number = qb.zz; return qb; }
function g<T extends any>(qb: T): T { qb.andWhere(1); return qb; }
declare const m: Bad;
const r = m.query<number>("x");
declare const a: any;
const r2 = a.query<number>("x");
const r3 = a<string>();
function h<T extends unknown>(qb: T) { qb.foo; }
