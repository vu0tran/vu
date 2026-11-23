export function step(index: number, direction: -1 | 1, n: -2n | 3n): number {
  const x: any = index;
  const y = -x;
  const z = -(direction as unknown as string);
  return index + direction + -direction + Number(y) + Number(z) + Number(-n);
}
