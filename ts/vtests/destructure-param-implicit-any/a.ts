// a destructuring parameter with no type and no contextual one: each binding any, TS7031
import { G } from './missing3';
declare const g: G;
declare const a: any;
export const r1 = g.calls.map(([, request]) => request.orderUuid);
export const r2 = a.map(({ x }, [y]) => x + y);
const n: number = r1;
export const r3 = a.map(({ p = 1, q: { z } }, [m]) => p + z + m);
export function h3({ v }, [w]) { return v + w; }
