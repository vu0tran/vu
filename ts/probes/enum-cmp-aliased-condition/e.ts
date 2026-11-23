import { TaskType } from './e2';

declare const h: { t: string; n: number } | null;
const isA = h?.t === TaskType.A;
export const y1 = isA && h.n;
export const y2 = isA ? h.n : 0;

declare const k: { t: string; n: number } | undefined;
const isB = k?.t === TaskType.B;
if (isB) {
  console.log(k.n);
}

declare const arr: string[];
export function g(hh: { t: string; n: number } | null) {
  const isC = hh?.t === TaskType.A;
  const ended = hh?.t === TaskType.B || hh?.n === 1;
  const act = isC && !ended && arr.some((x) => x === hh.t);
  const done = isC && (hh.t === TaskType.B || hh.n === 2);
  return [act, done];
}
