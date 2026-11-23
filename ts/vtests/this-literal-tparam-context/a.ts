// this in a method of a literal whose contextual type is the call's type parameter (mobx-state-tree's
// .actions(() => ({ ... }))): the literal's own type, its this-free annotated methods typed
type ModelActions = { [key: string]: Function };
declare function actions<A extends ModelActions>(fn: () => A): A;
const r = actions(() => ({
  add(n: number) { return n + 1; },
  run() {
    const v: string = this.add(1);
    return v;
  },
}));
const n: number = r;
