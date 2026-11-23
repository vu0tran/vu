export class Failure extends Error {
  /** @param {'a' | 'b'} stage */
  constructor(stage) {
    super('failed');
    this.stage = stage;
  }
}

export const arrow = (/** @type {number} */ n, label = 'x') => n + label.length;

export const rest = async (/** @type {string[]} */ ...args) => args.length;

export const obj = {
  /** @template T @param {(x: number) => T} work @param {number} n */
  run(work, n) {
    return work(n);
  },
  size(/** @type {string} */ s) {
    return s.length;
  },
};

/** @param {number} x */
const bad = (x) => {
  /** @type {string} */
  const y = x;
  return y;
};
bad(1);
