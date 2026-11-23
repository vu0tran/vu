type S = 'Author' | 'DOC' | 'X';
interface Ph { source_type?: S }
export const cmp = (o: Partial<Record<S, number>>) => (a: Ph, b: Ph) => {
  if (!o[a.source_type] || !o[b.source_type]) return 0;
  const v = o[a.source_type];
  const n: string = v;
  return o[a.source_type] - o[b.source_type];
};
declare const r: Record<S, number>;
declare const k: S | undefined;
const w = r[k];
const m: string = w;
