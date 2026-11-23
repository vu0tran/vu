export {};
declare function mk(): { k: "a" | "b" };
function f() {
  let k;
  ({ k } = mk());
  const d: number = k;
  let j;
  [j] = [mk().k];
  const e: number = j;
  let i;
  i = mk().k;
  const g: number = i;
}
