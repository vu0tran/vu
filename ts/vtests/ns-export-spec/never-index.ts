export {};
type A = never["x"];
const a: A = 1;
type B<T> = T extends string ? never : { x: number };
type C = B<"s">["x"];
const b: C = 1;
