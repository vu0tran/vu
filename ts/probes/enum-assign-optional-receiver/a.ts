import { Phone1 as P1 } from './e1';
import { Phone1 as P2, TaskType } from './e2';

interface Phone { number: string; type: P1 }
interface Ctx { primary?: Phone; phones: Phone[]; req: Phone }
const phone = { number: '1', type: P2.Mobile };
export const c1: Ctx = { primary: phone, phones: [phone], req: phone };
const primary = phone;
export const c2: Ctx = { primary, phones: [], req: phone };

declare const task: { taskType: string } | null;
export const b1 = task?.taskType === TaskType.A;
function f(): { taskType: string } | null { return null; }
const t2 = f();
export const b2 = t2?.taskType === TaskType.B;

type Res = { ok: true; data: Phone; err?: undefined } | { ok: false; err: string; data?: undefined };
export function r1(): Res { return { ok: true, data: phone }; }
type CtxI = Ctx & { extra: boolean };
export const c3: CtxI = { primary: phone, phones: [], req: phone, extra: true };
