export {};
interface M { a: { x: 1 }; script: { y: 2 } }
declare function ce<K extends keyof M>(t: K): M[K];
const v = ce('script');
const b: boolean = v;
const b2: boolean = ce('script');
