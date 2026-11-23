// The tsconfig's paths apply to a package's declaration files too: foo's `import "bar"` is
// bar's esm copy, the one the path names, so a class with a private member imported here from
// "bar/esm" (and from "bar", by the path) is the one foo takes. Without that, two copies of B
// that don't relate.
import { take } from "foo";
import { B } from "bar/esm";
import { B as B2 } from "bar";
declare const b: B;
take(b);
declare const b2: B2;
take(b2);
const n: number = b;
