export function A({ groups }: { groups: { n: number }[] }) {
  let sections = null;
  lbl: {
    if (groups.length) { sections = 1; break lbl; }
    let start = 0;
    sections = groups.map((g) => {
      start += g.n;
      return start;
    });
  }
  return <div>{sections}</div>;
}
