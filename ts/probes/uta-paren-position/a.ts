type W = { innerText?: string; textContent?: string | null };
export function f(n: W, rotation: number) {
  const t = ((n.innerText || n.textContent || '') as string).trim();
  const r = (((rotation % 360) + 360) % 360) as number;
  return t + r;
}
