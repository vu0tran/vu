// An assertion function whose variable is declared with a function type narrows what follows.
class Err extends Error {
  extensions: { [k: string]: unknown } = {};
}

const assertErr: (error: unknown) => asserts error is Err = (error) => {
  if (!(error instanceof Err)) throw error;
};
type AssertStr = (x: unknown) => asserts x is string;
const assertStr: AssertStr = (x) => {
  if (typeof x !== 'string') throw new Error();
};
const isNum: (x: unknown) => x is number = (x): x is number => typeof x === 'number';
const assertOk: (x: unknown) => asserts x = (x) => {
  if (!x) throw new Error();
};

export function f(u: unknown, v: string | undefined) {
  try {
    console.log(1);
  } catch (e) {
    assertErr(e);
    const x: number = e.extensions;
    const y: number = e.extensions.code;
  }
  if (isNum(u)) {
    const a: string = u;
  }
  assertOk(v);
  const b: number = v;
  assertStr(u);
  const c: number = u;
}
