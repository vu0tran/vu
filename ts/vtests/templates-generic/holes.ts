const RES = { wf: ['read', 'write'], cred: ['share'] } as const;
type RS<R extends keyof typeof RES> = `${R & string}:${(typeof RES)[R][number]}`;
export const a: RS<'wf'> = 'wf:read';
export const b: RS<'wf'> = 'wf:share';
export const c: RS<keyof typeof RES> = 'cred:share';
type G = { [R in keyof typeof RES]?: RS<R>[] };
export const g: G = { wf: ['wf:write'], cred: ['wf:read'] };
function f<K extends string>(k: K): `${K & string}!` { return null!; }
export const h: 'x!' = f('x');
export const h2: 'y!' = f('x');
