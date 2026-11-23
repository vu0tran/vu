import { useMemo } from 'react';
export function A({ groups }: { groups: { n: number }[] | null }) {
  const sections = useMemo(() => {
    if (!groups) return null;
    let start = 0;
    return groups.map((g) => {
      start += g.n;
      return start;
    });
  }, [groups]);
  return <div>{sections}</div>;
}
