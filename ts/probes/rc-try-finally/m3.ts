import { useCallback } from 'react';
declare function useRefresh(): () => Promise<void>;
declare function run(): Promise<number>;
export function useAct(id: string | undefined) {
  const refresh = useRefresh();
  const act = useCallback(async () => {
    if (!id) return undefined;
    try {
      const n = await run();
      if (n) return n;
    } catch {
      return undefined;
    } finally {
      await refresh();
    }
    return 0;
  }, [id, refresh]);
  return act;
}
