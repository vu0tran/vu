/** @implements {A} */
export function f1() {}


/** @implements {A} */
export const f2 = () => {};

/** @implements {A} */
export const f3 = function () {}, f4 = () => {};

const o = {
  /** @implements {A} */
  m() {},
  /** @implements {A} */
  get g() { return 1; },
  /** @implements {A} */
  p: function () {},
  /** @implements {A} */
  q: () => {},
};

class C {
  /** @implements {A} */
  m() {}
  /** @implements {A} */
  p = () => {};
  /** @param {number} [x=1] */
  constructor(x) {}
  /** @param {number} [y=2] */
  static s(y) {}
  /** @param {number} [z=2] */
  private async *gen(z) { yield z; }
}

/** @param [a=1] */
foo(() => {});

/** @param [a=1] */
(function (a) {})();


/** @implements {A} */
declare function decl(): void;

/** @param {string} [b="x"] */
function outer(b) {
  return function inner(c) {};
}

function host() {
  /** @param [d=1] */
  return (d) => d;
}

/** @param [e=1] */
new Thing((e) => e);

/** @implements {A} */ function sameLine() {}

foo(); /** @implements {A} */
function afterTrailing() {}

/** @param [g=1] */
namespace N { export function h(g) {} }

/** @param [h=1] */
export namespace M { export const z = (h) => h; }

/**
 * @yields {number}
 * @yields {number}
 */
function* dupY() { yield 1; }

/** Doc */
function* noY() { yield 1; yield 2; yield; }

/** Doc */
function* outerGen() {
  function inner() { return 3; }
  yield 5;
  const a = function* () { yield 4; };
}

/** Doc */
export function* expGen() { yield 1; }

/** Doc */
export async function* expAGen() { yield 1; }

const og = {
  /** Doc */
  *m() { yield 1; },
  /** Doc */
  async *n() { yield 1; },
};

class G {
  /** Doc */
  *m() { yield 1; }
  /** Doc */
  static async *[Symbol.iterator]() { yield 1; }
}

/** Doc */
const ge = function* () { yield 1; };

