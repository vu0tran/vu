export {};
type G1 = Promise<string> extends { then(a: any, ...args: any[]): any } ? 1 : 0;
const g1: G1 = 5;
type G2 = Promise<string> extends { then(onfulfilled: infer F): any } ? F : 0;
const g2: G2 = 5;
type G3 = Promise<string> extends { then(onfulfilled: infer F, ...args: infer R): any } ? R : 0;
const g3: G3 = 5;
interface P2<T> { then(cb: (v: T) => void): void }
type G4 = P2<string> extends { then(onfulfilled: infer F): any } ? F : 0;
const g4: G4 = 5;
