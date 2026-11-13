const RES = { wf: ['read', 'unpublish'], cred: ['share'] } as const;
type Resource = keyof typeof RES;
type RS<R extends Resource, O extends (typeof RES)[R][number] = (typeof RES)[R][number]> = `${R}:${O}`;
type All = { [R in Resource]: RS<R> };
type Scope = All[Resource];
export const s: ReadonlySet<Scope> = new Set(['wf:unpublish']);
type Scope2 = 'wf:read' | 'wf:unpublish' | 'cred:share';
export const s2: ReadonlySet<Scope2> = new Set(['wf:unpublish']);
export const s3: 'z' = null! as Scope;
