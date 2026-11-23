export function read(records: { id: string; n: number }[]) {
  let complete = true;
  const results = [];
  for (const r of records) {
    try { results.push({ id: r.id, twice: r.n * 2 }); } catch { complete = false; }
  }
  return { results, complete };
}
