import { useState } from 'react';
export function useRun(q: { run: () => Promise<string>; xs: number[] }) {
  const [s] = useState(0);
  const go = async () => {
    try {
      return await q.run();
    } catch {
      return 'failed';
    } finally {
      if (q.xs.length) {
        q.xs.sort((a, b) => a - b).forEach((x) => console.log(x + s));
      }
    }
  };
  return go;
}
