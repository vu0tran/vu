// A path in the tsconfig into node_modules names the file a package's own resolution finds: by
// its real path (pnpm's links), so the class imported both ways is one declaration, and its
// private member doesn't make the two unrelated.
import type { Map as M1 } from 'pkg';
import { Map as M2 } from 'pkg/esm';
declare const a: M2;
const b: M1 = a;
const n: number = b;
export { M2 };
