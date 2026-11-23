declare function run<R>(func: (...args: any[]) => R, ...args: any[]): R;
declare function run2<R>(func: (a: string) => R): R;
const f0 = (id: string) => {
  if (id) return { count: id.length };
  return { count: 1, selected: { key: id } };
};
export const b0 = f0('').selected;
export const a3 = run((id: string) => {
  if (id) return { count: id.length };
  return { count: 1, selected: { key: id } };
});
export const b3 = a3.selected;
export const a4 = run2((id) => {
  if (id) return { count: 2 };
  return { count: 1, selected: { key: id } };
});
export const b4 = a4.selected;
export const n4: number = a4.selected?.key;
export const a5 = run2((id) => {
  if (id) return { count: 2 };
  return { count: 1 };
});
export const n5: string = a5;
