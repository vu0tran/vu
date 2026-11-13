interface N { id: string; name: string; t?: number }
function mk({ anchor, ...o }: Partial<N> & { anchor: boolean }): N {
  const q: 'z' = o;
  return { id: o.id ?? 'a', name: o.name ?? 'n', t: o.t };
}
export { mk };
