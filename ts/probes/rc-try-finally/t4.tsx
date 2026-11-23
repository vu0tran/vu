import { useEffect } from 'react';
export function X({ a }: { a: number }) {
  const g = () => {
    try { bar(0); } finally { bar(z); }
  };
  useEffect(() => { g(); });
  const z = a;
  return <div>{a}</div>;
}
declare function bar(x: unknown): void;
