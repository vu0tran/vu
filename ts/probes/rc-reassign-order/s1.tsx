import { useMemo, useSyncExternalStore } from 'react';
type Api = { isVisible: boolean; onChange: (f: (v: boolean) => void) => { dispose: () => void } };
export function Panel({ api }: { api: Api }) {
  const visibility = useMemo(() => {
    let seen = api.isVisible;
    return {
      getSnapshot: () => {
        seen ||= api.isVisible;
        return seen;
      },
      subscribe: (notify: () => void) => {
        const s = api.onChange((v) => {
          seen ||= v;
          notify();
        });
        return () => s.dispose();
      },
    };
  }, [api]);
  const seen = useSyncExternalStore(visibility.subscribe, visibility.getSnapshot);
  return <div>{String(seen)}</div>;
}
