type T = 'a' | 'b';
interface N { t: T }
export const x: { [k: number]: N } = { '1': { t: 'a' }, 2: { t: 'b' } };
export const y: { [k: number]: N } = { '1': {} };
