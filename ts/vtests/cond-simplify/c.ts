export {};
function f<U extends string, V extends string | undefined, W extends { a: 1 }, X extends "a" | "b">(x: U & undefined, v: V & undefined, w: W & null, w2: W & string, xx: X & "c", xy: X & "a", u2: U & number, u3: U & "lit", u4: U & {}) {
  const a: [1] = [x, v, w, w2, xx, xy, u2, u3, u4];
}
