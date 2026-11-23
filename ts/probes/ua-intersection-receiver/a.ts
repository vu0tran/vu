import { Address, Lead } from './missing';
declare const ADDRESS: Address;
declare const LEAD: Lead;
type Base = { address: Address; n: number };
type Opts = Base & { lead: Lead };
class Model { constructor(o: Opts) { void o; } }
class Sub extends Model { constructor(o: Opts) { super(o); } }
export const m1 = new Model({ address: ADDRESS, n: 1, lead: LEAD });
export const m2 = new Sub({ address: ADDRESS, n: 1, lead: LEAD });
declare function f(o: Opts): void;
f({ address: ADDRESS, n: 1, lead: LEAD });
