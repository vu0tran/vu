function listFiles(dir) {
  const out = [];
  for (const name of ['a', String(dir)]) {
    if (name === 'x') out.push(...listFiles(name).map((f) => `${name}/${f}`));
    else out.push(name);
  }
  return out;
}

export const files = listFiles('a/b').filter((f) => f !== 'c');
if (!files.includes('d')) console.log(files);

function count(n) {
  if (n <= 0) return 0;
  return count(n - 1) + 1;
}
export const k = count(3);

function nest(n) {
  const r = [];
  r.push(n);
  if (n > 0) r.push(nest(n - 1).length);
  return r;
}
export const m = nest(2);
