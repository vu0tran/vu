// spreading Omit<any, K> (a mapped type over string | number | symbol), alone and in an intersection
export const w3 = (args: Omit<any, 'x'> & { x?: number }) => { const q: string = { ...args }; };
export const w4 = (args: Omit<any, 'x'>) => { const q: string = args; const r: string = { ...args }; };
