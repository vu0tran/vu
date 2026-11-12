export {};
type Un<T> = T extends Promise<infer U> ? Un<U> : T;
const y: Un<Promise<Promise<number>>> = 's';
type Th<T> = T extends { then(f: infer F): any } ? F extends (v: infer V) => any ? Th<V> : never : T;
const z: Th<Promise<Promise<number>>> = 's';
type Th2<T> = T extends { then(f: infer F): any } ? F : T;
const z2: Th2<Promise<Promise<number>>> = 's';
