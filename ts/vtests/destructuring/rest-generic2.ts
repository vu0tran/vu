type DN = { id: string; name: string; opt?: number; parameters: { [k: string]: unknown } };
declare function cmp(a: DN): boolean;
declare function cmpO(a: { id: string; opt: number }): boolean;
function f<T extends DN>(p: T) {
  const { id, ...rest } = p;
  cmp({ ...rest, id: 'x' });
  cmp({ ...rest });
  cmpO(rest);
  const r2: { name: string } = rest;
  const r3: { id: string } = rest;
  return id;
}
export { f };
