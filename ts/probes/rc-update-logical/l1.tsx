export function A({ groups, k }: { groups: { n: number }[]; k: string }) {
  const obj: Record<string, number[]> = {};
  obj.x ||= [1];
  obj[k] ??= [];
  let n = 0;
  n ||= groups.length;
  let m = 1;
  m &&= groups.length;
  return <div>{obj.x.length}{n}{m}</div>;
}
