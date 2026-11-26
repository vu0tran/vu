export function build(xs: number[]) {
  const out = [];
  for (const x of xs) {
    out.push({ v: x });
  }
  return { out };
}
