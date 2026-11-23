export function A({ groups }: { groups: { n: number }[] }) {
  let v = true;
  const s = groups.map((g) => { v &&= g.n > 0; return v; });
  return <div>{s.length}</div>;
}
