export function A({ groups }: { groups: { n: number }[] }) {
  let start = 0;
  let f = () => {};
  let i = 0;
  while (i < groups.length) { const h = f; f = () => { start += 1; }; i++; if (h) break; }
  return <div onClick={f} />;
}
