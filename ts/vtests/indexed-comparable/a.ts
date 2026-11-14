function f1<T extends object>(x: T[keyof T]) { return x as T; }
function f2<T>(x: T[keyof T]) { return x as T; }
function f3<T extends { a: number }>(x: T[keyof T]) { return x as T; }
function f4<T extends object, U extends object>(x: U[keyof U]) { return x as T; }
function f5<T extends object>(x: T) { return x as T[keyof T]; }
function f6<T extends object>(x: T["a" & keyof T]) { return x as T; }
function f7<T extends object>(x: T[keyof T]) { return x as string; }
function f8<T extends object>(x: T[keyof T]) { return 1 as T[keyof T]; }
function f9<T extends object>(x: T[keyof T]) { return x as T[keyof T][]; }
function g1<T extends { a: number }>(x: T["a"]) { return x as string; }
function g2<T extends { a: number }>(x: T) { return x as T["a"]; }
function g3<T extends object>(x: string) { return x as T[keyof T]; }
function g4<T extends object>(x: T[keyof T], y: T[keyof T]) { return x === y; }
function g5<T extends object>(x: T[keyof T]) { if (x === 1) return 1; return 0; }
export {};
