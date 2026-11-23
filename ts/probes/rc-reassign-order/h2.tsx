declare function useX(a: unknown, b: unknown): void;
export function A({ n }: { n: number }) {
  let x = 0;
  let y = 0;
  const f1 = () => { x = 1; };
  const f2 = () => { y = 1; };
  useX(f2, f1);
  return <div>{n}</div>;
}
