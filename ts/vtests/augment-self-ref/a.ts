import { expect } from './m';
declare module './m' {
  interface Statics {
    soft: <T>(v: T) => Assertion<void, T>;
  }
  interface Assertion<R, T> {
    snap(): R;
  }
  interface Assertion<R, T> {
    snap2(): R;
  }
}
declare const st: import('./m').Statics;
const s = st.soft(1);
s.not.toBe(2);
s.base;
s.snap();
s.snap2();
s.toBe('x');
expect(1).snap2();
const n: null = s;
