// A variable initialized with a function reads as that function in the function's own return
// expressions (tsc has its type before its return type): node.forEach(walk) is a call with a
// function; w3 in [n].map(w3) asks for its own return type: any, TS7023.
export function f(tree: unknown) {
  const walk = (node: unknown) => {
    if (Array.isArray(node)) return node.forEach(walk);
  };
  walk(tree);
  const w3 = function (n: number) {
    return [n].map(w3).length + w3.nope;
  };
  return [w3];
}
