type F = (a: number, o?: { x: 1 }) => string;
export const f: F = (a, o) => { const z: { x: 1 } = o; return '' + a + z; };
export const g: F = (a, o) => '' + a + o?.x;
