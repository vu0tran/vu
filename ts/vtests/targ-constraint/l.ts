export {};
type X = Pick<{ a: 1 }, "b">;
interface I<T extends string> { t: T }
let y: I<number>;
