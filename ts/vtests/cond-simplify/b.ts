export {};
function f<U extends string>(x: U & undefined, y: U & null, z: U & number) { const n: never = x; const n2: never = y; const n3: never = z; }
function g<U>(x: U & undefined) { const n: never = x; }
