type H = { a?: (x: number) => void; b?: (s: string) => void };
function r2<K extends keyof H>(z: H[K] & ({} | null), z2: H[K] & null, z3: H[K] & {}) {
  const w: NonNullable<H[K]> = z;
  const w2: NonNullable<H[K]> = z2;
  const w3: NonNullable<H[K]> = z3;
  const n: number = z2;
  const n2: [] = z;
}
function r5<T extends string | undefined>(z: T & ({} | null), z2: T & null) {
  const w: NonNullable<T> = z;
  const n: number = z2;
}
export {};
