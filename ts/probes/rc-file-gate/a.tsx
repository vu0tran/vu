import { memo } from 'react';
export default memo(function Clock({ a }: { a: number }) {
  const t = Date.now();
  return <div>{t}{a}</div>;
});
