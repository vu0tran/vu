export const D = ['create', 'read'] as const;
declare const arr: string[];
declare const opt: [1, 2?];
export const R = {
	agent: [...D, 'execute'] as const,
	b: [...D] as const,
	c: ['x', ...D, ...D] as const,
	d: [1, ...arr] as const,
	e: [...opt, 3] as const,
};
const b1: boolean = R;
type K = (typeof R)[keyof typeof R][number];
const b2: boolean = null! as K;
