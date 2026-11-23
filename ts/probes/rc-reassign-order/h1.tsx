export function A({ n }: { n: number }) {
  let x = 0;
  let y = 0;
  const f1 = () => { x = 1; };
  const f2 = () => { y = 1; };
  return <div onClick={f2} onKeyDown={f1}>{n}</div>;
}
