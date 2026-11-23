import { useCallback } from 'react';
declare function useRefresh(): () => Promise<void>;
declare function run(): Promise<number>;
export function useAct(id: string | undefined) {
  const refresh = useRefresh();
  const act = useCallback(async () => {
    try {
      await run();
    } finally {
      await refresh();
    }
  }, [id, refresh]);
  return act;
}
