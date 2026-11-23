export function A({ groups }: { groups: { n: number }[] }) {
  let start = 0;
  let s = null;
  if (groups.length) { s = () => { start += 1; }; } else { s = () => { start += 2; }; }
  return <div onClick={s} />;
}
