declare const x: { a?: 1; b: 2 };
const y: { a: 1 | undefined } = x;
type R = { a?: 1; b: 2 } extends Record<'a', 1 | undefined> ? 't' : 'f';
const z: 5 = null as unknown as R;
type R2 = { a?: 1; b: 2 } extends { a: 1 | undefined } ? 't' : 'f';
const z2: 5 = null as unknown as R2;
export {};
