// null and undefined comparisons on a type parameter: T & ({} | null), NonNullable<T>, ??, instanceof
export {};
function q<T>(x: T, y: T & null, z: T & {}) { const e: {} = x; const e2: {} = y; const e3: {} = z; const e4: object = z; }
function r<T>(y: T | undefined, d: number) { const z = y ?? d; const n: string = z; const w = y ?? y; const m: string = w; }
