interface F { devices: string[]; truncated: boolean }
declare function fa(): Promise<F>;
declare function fb(): Promise<number[]>;
declare const ready: boolean;
async function main() {
  const [off, sug] = ready
    ? await Promise.all([fa(), fb()])
    : [{ devices: [], truncated: false }, []];
  const x: null = off;
  const y: null = sug;
  const [p, q] = ready ? [1, 'a'] : [{ devices: [], truncated: false }, []];
  const z: null = p;
  const w: null = q;
}
