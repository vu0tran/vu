// a binding element's default reading an earlier element of the same pattern: declared before
// (isBlockScopedNameDeclaredBeforeUse), with the type that element was bound with
export {};
declare const e: { s?: boolean; c?: boolean };
const { s = false, c = s } = e;
const a: never = c;
let { s3 = 1, c3 = s3 } = { s3: 2 } as { s3?: number; c3?: number };
const d: never = c3;
function g(execution: { s?: boolean; c?: boolean } = {}) {
  const { s = false, c = s } = execution;
  const a: string = c;
}
