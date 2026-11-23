import { useEffect } from 'react';
declare function foo(): void;
export function useF(q: { loading: boolean }) {
  useEffect(() => {
    refresh();
  });
  function refresh() {
    if (!loading) foo();
  }
  const loading = q.loading;
  return loading;
}
