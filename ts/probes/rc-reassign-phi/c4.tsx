export function A({ groups }: { groups: { n: number }[] }) {
  let start = 0;
  let f = () => {};
  for (const x of groups) { if (x.n) f = () => { start += x.n; }; }
  return <div onClick={f} />;
}
