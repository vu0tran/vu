export function X({ a }: { a: number }) {
  let x1 = 0;
  let x2 = 0;
  const f1 = () => { x1 = 1; };
  const f2 = () => { x2 = 1; };
  let y = null;
  let z = null;
  try { y = <div onClick={f1} />; } finally { z = <div onClick={f2} />; }
  return <div>{a}{y}{z}</div>;
}
