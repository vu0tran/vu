// f(...x) to <E extends any[]>(...args: E): E is x's type
declare function called<E extends any[]>(...args: E): E;
declare function strs<E extends string[]>(...args: E): void;
export function f(args: [string, number] | [null], b: [1] | number[]) {
  const r: null = called(...args);
  const r2: null = called(...b);
}
