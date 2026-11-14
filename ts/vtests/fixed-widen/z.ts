declare function g<T>(x: T, c?: { m?: (v: T) => void }): T[];
const r3: number = g(1, { m: (v) => { const s: string = v; } });
export {};
