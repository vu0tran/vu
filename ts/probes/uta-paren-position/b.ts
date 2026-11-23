export type PageRotation = 0 | 90 | 180 | 270;
export function normalizeRotation(rotation: number): PageRotation {
  const r = (((rotation % 360) + 360) % 360) as number;
  if (r === 90 || r === 180 || r === 270) return r;
  return 0;
}
