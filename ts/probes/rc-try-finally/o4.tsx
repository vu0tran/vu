export function X({ a }: { a: number }) {
  let x1 = 0;
  const f1 = () => { x1 = 1; };
  let y = null;
  try { bar(); } finally { return <div onClick={f1} />; }
  return <div>{a}{y}</div>;
}
declare function bar(): void;
