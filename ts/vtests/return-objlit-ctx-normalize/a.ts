// Object literals returned by a function with a contextual return type (a generic call's T):
// reduced by subtypes as returned (count: 0 and count: 1 are different literals), then given each
// other's missing properties, optional and undefined (getWidenedType of the union).
declare const flag: boolean;
declare function ev<T>(f: () => T): T;
export const r3 = ev(() => {
  if (flag) return { count: 0 };
  return { count: 1, selected: { key: 'k', text: 'x' } };
});
export const a3: number = r3.selected;
export const r5 = ev(() => {
  if (flag) return { count: 0, kind: 'a' };
  return { count: 1, other: true };
});
export const a5: number = r5.other;
export const a6: number = r5.kind;
