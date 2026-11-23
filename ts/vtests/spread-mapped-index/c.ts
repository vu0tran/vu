import { nope } from './missing';
type R = Parameters<typeof nope>[1];
type A = Omit<R, 'x'> & { x?: number };
export const w = (args: A) => { const q: string = args; const r: string = { ...args }; };
