import { useCallback, useState } from 'react';
export function Settle({ onDone }: { onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  let attempt = 0;
  const run = useCallback(() => {
    attempt += 1;
    setBusy(true);
    onDone();
  }, [onDone]);
  return <button disabled={busy} onClick={run}>{attempt}</button>;
}
