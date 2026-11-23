export function A({ groups }: { groups: { n: number }[] }) {
  let j = 0;
  const s = groups.map((g) => g.n + j++);
  return <div>{s.length}</div>;
}
