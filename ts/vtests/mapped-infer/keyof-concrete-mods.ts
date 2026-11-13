interface O { a?: string; b?: number; c: boolean }
declare function g<K extends keyof O>(...k: K[]): { [P in K]: NonNullable<O[P]> };
export const z: 'z' = g('a');
