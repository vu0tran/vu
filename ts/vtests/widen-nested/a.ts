export {};
declare function each<T>(cases: ReadonlyArray<T>): (fn: (arg: T) => void) => void;
each([
  { name: "a", data: { name: "x" } },
  { name: "b", data: { config: { p: 1 } } },
  { name: "c", data: {} },
])(({ data }) => {
  const n: number = data.name;
  const c: number = data.config;
});
const arr = [{ data: { name: "x" } }, { data: {} }];
const m: number = arr[0].data.name;
declare function id<T>(x: T): T;
const r = id([{ data: { name: "x" } }, { data: {} }]);
const m2: number = r[0].data.name;
