export class A extends Error {
  constructor(m: string) {
    super(m);
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, A);
    }
  }
}
export class B extends TypeError {
  constructor() { super(); Error.captureStackTrace(this, this.constructor); }
}
export class C extends Error {
  constructor() { super(); Error.captureStackTrace(this, new.target); }
}
export class D extends Error {
  constructor() { super(); Error.captureStackTrace(this, Other); }
}
export class E extends MyErr {
  constructor() { super(); Error.captureStackTrace(this, E); }
}
export class F extends Error {
  constructor() { super(); const f = () => Error.captureStackTrace(this, F); f(); }
}
export class G extends Error {
  constructor() { super(); function g(this: any) { Error.captureStackTrace(this, G); } g(); }
}
export class H extends Error {
  method() { Error.captureStackTrace(this, H); }
}
export class I extends Error {
  constructor() { super(); Error.captureStackTrace(this); }
}
export class J extends Error {
  constructor() { super(); Error.captureStackTrace(other, J); }
}
export const K = class extends Error {
  constructor() { super(); Error.captureStackTrace(this, K); }
};
export const L2 = class LL extends Error {
  constructor() { super(); Error.captureStackTrace(this, LL); }
};
export class M extends Error {
  constructor() { super(); Error?.captureStackTrace(this, M); }
}
export class N extends Error {
  constructor() { super(); Error.captureStackTrace?.(this, N); }
}
export class O extends Error {
  constructor() { super(); Error['captureStackTrace'](this, O); }
}
export class P extends AggregateError {
  constructor() { super([]); Error.captureStackTrace(this, P); }
}
export class Q extends Error {
  constructor() { super(); class R { constructor() { Error.captureStackTrace(this, Q); } } }
}
export class S extends Error {
  constructor() { super(); const x = Error.captureStackTrace(this, S); }
}
export class T extends Error {
  static { Error.captureStackTrace(this, T); }
}
export class U extends globalThis.Error {
  constructor() { super(); Error.captureStackTrace(this, U); }
}
export class V extends Error {
  constructor() { super(); Error.captureStackTrace(this, V, 1); }
}
export class W extends Error {
  x = Error.captureStackTrace(this, W);
}
export class X extends Error {
  constructor() { super(); Error.captureStackTrace(this, this.constructor.name); }
}
export class Y extends Error {
  constructor() { super(); Error.captureStackTrace(...[this, Y]); }
}
export class Z extends SuppressedError {
  constructor() { super(1,2); Error.captureStackTrace(this, Z); }
}
export class Z2 extends DOMException {
  constructor() { super(); Error.captureStackTrace(this, Z2); }
}
export class Z3 extends Error {
  constructor() { super(); Error.captureStackTrace((this), (Z3)); }
}
export class Z4 extends InternalError {
  constructor() { super(); Error.captureStackTrace(this, Z4); }
}
