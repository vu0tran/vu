// a property of a variable with a type annotation assigned in a loop that exits only by break:
// tracked through the loop (the variable's type is its annotation), after it the break states'
export {};
declare function next(): { model?: string; done: boolean };
function f() {
  const parsed: { model?: string; usage?: number } = {};
  while (true) {
    const chunk = next();
    if (chunk.model) parsed.model = chunk.model;
    if (chunk.done) break;
  }
  parsed.model.length;
}
function g() {
  const p: { model?: string } = {};
  while (true) {
    p.model = "x";
    break;
  }
  const m: number = p.model;
}
