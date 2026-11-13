type DN = { id: string; name: string; parameters: { [k: string]: unknown } };
declare function cmp(a: DN, b: DN): boolean;
function sup<T extends DN>(p: T, n: T) {
  const { parameters: pp, ...prev } = p;
  const { parameters: np, ...next } = n;
  const q: 'z' = prev;
  if (!cmp({ ...prev, parameters: {} }, { ...next, parameters: {} })) return false;
  return [pp, np];
}
export { sup };
