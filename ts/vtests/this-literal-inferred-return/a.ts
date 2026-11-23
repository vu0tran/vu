// this in a method of a literal a function argument returns, the function's return the call's type
// parameter (mobx-state-tree's .actions(self => ({ ... }))): the literal, as tsc's deferred check of
// the method bodies sees it, not the parameter's constraint
type ModelActions = { [key: string]: Function };
interface Model<P, O> {
  actions<A extends ModelActions>(fn: (self: P & O) => A): Model<P, O & A>;
}
declare const store: Model<{ log: string[] }, {}>;
export const S = store.actions((self) => ({
  _addLogEntry(entry: { id: string }) {
    self.log.push(entry.id);
    return self.log.length;
  },
  addExternalLogEntry(entry: { id: string }) {
    const n: string = this._addLogEntry(entry);
    return n;
  },
}));
export const S2 = store.actions((self) => {
  return {
    one(): number { return self.log.length; },
    two() { const s: string = this.one(); return s; },
  };
});
