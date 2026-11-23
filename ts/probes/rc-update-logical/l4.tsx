export function A({ groups }: { groups: { n: number }[] }) {
  let j = 0;
  const s = groups.map((g) => { const x = j++; return g.n + x; });
  const t = groups.map((g) => { const y = ++j; return g.n + y; });
  return <div>{s.length}{t.length}</div>;
}
