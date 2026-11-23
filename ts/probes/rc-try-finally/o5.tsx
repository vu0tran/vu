export function X({ a }: { a: number }) {
  let x1 = 0;
  const f1 = () => { x1 = 1; };
  try { return null; } finally { bar(<div onClick={f1} />); }
}
declare function bar(x: unknown): void;
