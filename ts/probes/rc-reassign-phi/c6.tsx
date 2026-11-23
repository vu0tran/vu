export function A({ groups }: { groups: { n: number }[] }) {
  let start = 0;
  let f = () => { start += 1; };
  f();
  f = () => {};
  return <div onClick={f} >{groups.length}</div>;
}
