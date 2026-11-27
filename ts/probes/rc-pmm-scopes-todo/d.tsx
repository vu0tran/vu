import { useMemo } from 'react';
export function Cases({ k, items }: { k: string; items: number[] }) {
  const v = useMemo(() => {
    let total = 0;
    for (const i of items) {
      if (i < 0) return -1;
      total += i;
    }
    return total;
  }, [items]);
  switch (k) {
    case 'a':
      return <b>{v}</b>;
    default:
      return <i>{v}</i>;
  }
}
