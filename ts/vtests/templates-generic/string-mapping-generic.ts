type EP = 'workflowSave' | 'credentialSave';
export type M = `on${Capitalize<EP>}`;
export const z: 'z' = null as unknown as M;
export const E: { readonly [P in EP]: `on${Capitalize<P>}` } = { workflowSave: 'onWorkflowSave', credentialSave: 'onCredentialSave' };
export const bad: { readonly [P in EP]: `on${Capitalize<P>}` } = { workflowSave: 'onWorkflowSave', credentialSave: 'onX' };
type G<T extends string> = Uppercase<T>;
export const g: 'z' = null as unknown as G<'ab'>;
export function f<T extends string>(t: T): `get${Capitalize<T>}` { return null as any; }
export const h: 'z' = f('name');
type GG<T extends string> = { k: `x${Lowercase<T>}` };
export const gg: 'z' = null as unknown as GG<'AB'>;
