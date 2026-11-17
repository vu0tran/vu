// a labeled block left by break: not modeled (the file is left unchecked)
export function f(n: number) {
  let q: string | number = 1;
  blk: { if (n) { q = 's'; break blk; } }
  const qq: null = q;
}
