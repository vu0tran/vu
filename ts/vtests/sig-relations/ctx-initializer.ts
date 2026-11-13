type F = (a: number, o?: { x?: 1 }) => string;
export const f: F = (a, o = {}) => { const z: { x?: 1 } = o; return '' + a + z; };
type G = (a: number, o?: { x?: 1 } | undefined | null) => string;
export const g: G = (a, o = {}) => { const z: { x?: 1 } | null = o; return '' + a + z; };
