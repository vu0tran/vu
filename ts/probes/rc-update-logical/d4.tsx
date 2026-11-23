export function A({ groups }: { groups: { n: number }[] }) {
  let v = 0;
  const s = groups.map((g) => { v ??= g.n; return v; });
  return <div>{s.length}</div>;
}
