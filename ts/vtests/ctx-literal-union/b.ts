type OptB = { a: { x?: number }; b: { y?: string } };
type UB1 = { [Name in keyof OptB]: { name: Name; params?: OptB[Name] } }[keyof OptB];
export const e1: UB1 = { name: 'a', params: { x: 1 } };
type UB2 = UB1 | { name: string; fn: () => void };
export const e2: UB2 = { name: 'a', params: { x: 1 } };
type OptB3 = { a: { x?: number } } & { b: { y?: string } };
type UB3 = { [Name in keyof OptB3]: { name: Name; params?: OptB3[Name] } }[keyof OptB3] | { name: string; fn: () => void };
export const e3: UB3 = { name: 'a', params: { x: 1 } };
