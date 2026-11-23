export function A({ groups }: { groups: { n: number }[] }) {
  const a = groups.length;
  a ||= 1;
  return <div>{a}</div>;
}
