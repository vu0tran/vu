import { useMemo } from 'react';
export function A({ groups }: { groups: { n: number }[] | null }) {
  const sections = useMemo(() => {
    if (!groups) return null;
    let start = 0;
    return groups.map((g) => {
      const s = { g, start };
      start += g.n;
      return s;
    });
  }, [groups]);
  return <div>{sections?.length}</div>;
}
