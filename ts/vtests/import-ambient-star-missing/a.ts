// a named import of a name an ambient module doesn't export through its export * (an older
// @types/node's node:fs without globSync): TS2305, the error type
import { existsSync, globSync, sep } from 'node:fs2';
import { here, gone } from 'node:other';
const a: number = existsSync;
const b: number = globSync;
const s: number = sep;
for (const m of globSync('x')) {
  const n: number = m;
}
const g: number = gone;
here();
