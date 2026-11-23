import { useEffect } from 'react';
export function X({ a }: { a: number }) {
  const g = () => {
    try { bar(0); } catch { bar(z); } finally { bar(1); }
  };
  useEffect(() => { g(); });
  const z = a;
  return <div>{a}</div>;
}
declare function bar(x: unknown): void;
