declare function fail(m: string): never;
export const p2 = <T>(v: T) => {
  if (v === null) throw fail('y');
  const n: number = v;
};
export const p3 = <T>(v: T) => {
  if (typeof v !== 'object') throw fail('y');
  const n: number = v;
};
export const p4 = <T>(v: T) => {
  if (typeof v === 'object') { const n: number = v; }
  if (typeof v === 'string') { const n: number = v; }
  if (typeof v !== 'string') { const n: number = v; }
  if (typeof v === 'function') { const n: number = v; }
};
export const p5 = <T>(v: T) => {
  if (v === null || typeof v !== 'object') throw fail('y');
  const n: number = v;
};
