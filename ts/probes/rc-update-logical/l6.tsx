import { useMemo } from 'react';
export function A({ items }: { items: { k: string }[] }) {
  const counts = useMemo(() => {
    const m: Record<string, number> = {};
    for (const it of items) {
      m[it.k] ??= 0;
      m[it.k] += 1;
    }
    return m;
  }, [items]);
  let seen = false;
  const onClick = () => {
    seen ||= true;
  };
  return <div onClick={onClick}>{Object.keys(counts).length}</div>;
}
