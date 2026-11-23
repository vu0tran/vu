import { useEffect } from 'react';
declare function foo(x: unknown): void;
export function useX(a: boolean, b: boolean) {
  const obj = {};
  const refresh = () => {
    if (!loading) foo(obj);
  };
  useEffect(() => {
    refresh();
  });
  const loading = a || b;
  return {};
}
