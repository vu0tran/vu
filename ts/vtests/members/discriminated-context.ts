// A union contextual type discriminated by the literal's literal-valued discriminants and the
// optional ones it leaves out; optional never properties discriminate as undefined
interface Cl { readonly scope: 'cluster'; readonly scheduler: { retry: boolean }; readonly lt?: number; readonly it?: never; }
interface Lt { readonly scope: 'cluster'; readonly scheduler?: never; readonly lt: number; readonly it?: never; }
interface In { readonly scope: 'instance'; readonly it: readonly [string, ...string[]]; readonly scheduler?: never; readonly lt?: never; }
type T = Cl | Lt | In;
const a: T = { scope: 'cluster' };
const b: T = {
  scope: 'cluster',
  scheduler: { retry: true },
  it: ['worker'],
};
