// a module augmentation of interfaces (declare module "./m" { ... })
import { mk } from './m';
declare module './m' {
	export interface Req { extra: string; raw(): Promise<void> }
}
const r = mk();
const n: number = r.extra;
const p: number = r.raw();
const q: string = r.a;
export {};
