declare const one2: { kind: 'a'; n: 1; b: true };
type T = typeof one2.kind;
const z: T = 'zz';
const z2: typeof one2.n = 5;
const z3: typeof one2.b = false;
const z4: number = null as unknown as T;
export { z, z2, z3, z4 };
