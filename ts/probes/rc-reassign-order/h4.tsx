export function A({ n }: { n: number }) {
  let y = 0;
  let x = 0;
  const f1 = () => { x = 1; };
  const f2 = () => { y = 1; };
  const o = { a: f2, b: f1 };
  return <div onClick={o.a}>{n}</div>;
}
