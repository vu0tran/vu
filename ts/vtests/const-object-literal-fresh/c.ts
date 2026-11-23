export const D = [
  { key: 'a', width: 1, locked: true },
  { key: 'b', width: 2 },
] as const;
export function isLocked(key: string): boolean {
  const column = D.find((c) => c.key === key);
  if (!!column && 'locked' in column) { const q: string = column.locked; }
  return false;
}
const E = [{ a: 1 }, { b: 2 }] as const;
const x = E[0];
const q2: string = x;
