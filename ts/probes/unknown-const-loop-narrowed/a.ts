// an unknown for-of const narrowed by typeof in a loop: its narrowing is exact
export function f(entries: [string, unknown][]): string[] {
  const lines: string[] = [];
  for (const [k, v] of entries) {
    if (v != null && typeof v === 'object') lines.push(k);
    else lines.push(`${k}: ${v}`);
  }
  return lines;
}
