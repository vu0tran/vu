export const f = (options?: { v?: number }) => {
  if (options?.v !== undefined) { const q: number = options.v; return q; }
  return 1;
};
export const g = <T,>(options?: { v?: T }) => {
  if (options?.v !== undefined) { const q: T = options.v; return q; }
  return 1;
};
export const h = (options?: { v?: number }) => {
  if (options?.v != null) { return options.v; }
  if (options?.v) { return options.v; }
  if (typeof options?.v === 'number') { return options.v; }
  if (options?.v === 1) { return options.v; }
  return 1;
};
