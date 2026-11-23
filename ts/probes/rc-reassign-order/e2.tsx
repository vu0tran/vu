export function A({ n }: { n: number }) {
  let x = 0;
  let y = 0;
  const f1 = () => { x = 1; };
  const f2 = () => { y = 1; };
  const o = [f1, f2];
  return <div onClick={o[0]}>{n}</div>;
}
