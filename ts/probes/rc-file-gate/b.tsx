import { forwardRef } from 'react';
export const Box = forwardRef<HTMLDivElement, { n: number }>((props, ref) => {
  const t = Math.random();
  return <div ref={ref}>{t}{props.n}</div>;
});
