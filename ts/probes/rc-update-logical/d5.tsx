export function A({ groups }: { groups: { n: number }[] }) {
  let j = 0;
  const s = groups.map((g) => { ++j; return g.n; });
  return <div>{s.length}</div>;
}
