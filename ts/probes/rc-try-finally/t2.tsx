export function X({ a }: { a: number }) {
  let x = 0;
  const f = () => { x = 1; };
  let y = null;
  try { bar(); } finally { y = <div onClick={f} />; }
  return <div>{a}{y}</div>;
}
declare function bar(): void;
