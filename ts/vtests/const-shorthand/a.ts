// shorthand properties in an as const object; a single-quoted string there prints as written
const w = 'w';
export const l1 = { type: 'execution', w } as const;
export const l2 = { type: 'execution', w: 'w' } as const;
export const l3 = { type: 'execution' } as const;
export const l4 = ['a', 'b'] as const;
export const q1: number = l1;
export const q2: number = l2;
export const q3: number = l3;
export const q4: number = l4;
