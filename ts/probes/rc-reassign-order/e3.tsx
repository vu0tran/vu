export function A({ n }: { n: number }) {
  let x = 0;
  let y = 0;
  const o = { a() { x = 1; }, b: () => { y = 1; } };
  return <div onClick={o.a}>{n}</div>;
}
