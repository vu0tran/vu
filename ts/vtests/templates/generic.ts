export const RES = { wf: ['create', 'read'] as const, cred: ['share'] as const };
export type Resource = keyof typeof RES;
export type ResourceScope<R extends Resource, Op extends string = (typeof RES)[R][number]> = `${R}:${Op}`;
export type All = { [R in Resource]: ResourceScope<R> }[Resource];
const a: boolean = null! as All;
const b: ResourceScope<'wf'> = 'wf:create';
const c: ResourceScope<'wf'> = 'wf:share';
type W<T extends string> = `x-${T}` | `y-${T}`;
const d: boolean = null! as W<'a' | 'b'>;
function g<T extends string>(t: T): `p${T}` { return `p${t}` as `p${T}`; }
const e: boolean = g('q');
