export function A({ n }: { n: number }) {
  let x = 0;
  let y = 0;
  const f1 = () => { x = 1; };
  const f2 = () => { y = 1; };
  const o = { a: f1, b: f2 };
  return <div onClick={o.a}>{n}</div>;
}
