type Cron = '* * *' | `${number} ${number} *` | `${number} * *`;
declare const n: number;
declare const s: string;
export const c1: Cron = `${n} * *`;
export const c2: Cron = `${n} ${n} *`;
export const c3: Cron = `${s} * *`;
export const c4: Cron = `${n}-${n} * *`;
function f(): Cron { return `${n} * *`; }
export const c5: `a${string}` = `a${s}`;
export const c6: `a${string}` = `b${s}`;
export const c7: 'a1' = `a${1}`;
export const c8: 'a1' = `a${2}`;
export const c9: `x${boolean}` = `x${true}`;
export { f };
