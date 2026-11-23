import { mk, mk3 } from './m2';
const o = mk(async () => 1);
const n: string = o.get('a');
const o3 = mk3(() => 1);
const n3: string = o3.get('a');
