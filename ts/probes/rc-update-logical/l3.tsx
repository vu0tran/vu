let g = 0;
export function A({ groups }: { groups: { n: number }[] }) {
  g ||= groups.length;
  return <div>{g}</div>;
}
