// an unresolved module's names are the error type
import { Foo, bar, mk } from '@gql';
type Extras = Record<string, unknown>;
declare function setExtras(e: Extras): void;
declare function take(e: { [k: string]: number }): void;
export function f(input: Foo, loose: any) {
  // receivers from the contextual type's index signature
  setExtras({ input });
  setExtras({ a: loose, 0: input });
  take({ input, b: loose });
  // a literal spreading the error type is any, and its properties' receivers are their own types
  const q = { ...bar, x: 1, y: loose, z: input };
  let r: Foo;
  r = { ...mk(), id: loose };
  return [q, r];
}
