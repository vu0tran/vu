type R = { close: () => void } & { data: (c: string) => void };
type X<K> = K extends keyof R ? R[K] : never;
type I<K> = R[K & keyof R];
type Y = I<any>;
const y: string = null as unknown as Y;
type S = ({ [k: string]: number } & { a: 1 });
type SI<K> = S[K & string];
const z: string = null as unknown as SI<any>;
export {};
