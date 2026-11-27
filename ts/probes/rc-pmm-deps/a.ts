import { useMemo } from 'react';
export function useLimit({ job }: { job?: { start?: number; kind?: number } | null }) {
  const limit = useMemo(() => {
    if (!job?.start || job.kind !== 2) return 0;
    const s = convert(job.start);
    return s > 1 ? s : 0;
  }, [job?.start, job?.kind]);
  return { limit };
}
