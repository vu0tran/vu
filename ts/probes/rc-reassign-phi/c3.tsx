export function A({ groups }: { groups: { n: number }[] }) {
  let start = 0;
  const f = () => { start += 1; };
  const g = groups.length ? f : null;
  return <div onClick={g ?? undefined} />;
}
