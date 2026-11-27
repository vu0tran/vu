export function Stamp({ a }: { a: number }) {
  const t = Date.now();
  return <div>{t}{a}</div>;
}
