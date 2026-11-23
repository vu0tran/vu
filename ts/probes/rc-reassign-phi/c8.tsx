export function A({ groups }: { groups: { n: number }[] }) {
  let start = 0;
  let f = () => {};
  let g = () => {};
  for (const x of groups) { g = f; if (x.n) f = () => { start += x.n; }; }
  return <div onClick={g} />;
}
