// an intersection indexed while instantiating: a key no member has reads unknown; a member any
// makes it any
import { Missing } from './missing';
export {};
interface User { Defaults: 'v3' | 'v4'; Scalars: { [k: string]: { Input: unknown } }; Auth: object }
interface Ext<P extends Partial<User>> { Defaults: P['Defaults'] & ('v3' | 'v4'); Auth: P['Auth'] & {} }
interface ZT { Auth: { a: boolean }; Context: object }
type V = Ext<Omit<ZT, 'Auth'> & { Auth: { v: 'r' } }>;
declare const d: V['Defaults'];
const n1: number = d;
declare const a: V['Auth'];
const n2: number = a;
type Sc<P extends Partial<User>> = { [K in keyof P['Scalars' & keyof P]]: 1 };
declare const m: Ext<Missing & Missing>;
const n3: number = m.Defaults;
