export function A({ groups }: { groups: { n: number }[] }) {
  let start = 0;
  let sections = null;
  if (groups.length) sections = groups.map((g) => { start += g.n; return start; });
  return <div>{sections}</div>;
}
