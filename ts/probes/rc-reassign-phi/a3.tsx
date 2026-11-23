export function A({ groups }: { groups: { n: number }[] }) {
  let sections = null;
  if (groups.length) {
    let start = 0;
    sections = groups.map((g) => {
      start += g.n;
      return start;
    });
  }
  return <div>{sections}</div>;
}
