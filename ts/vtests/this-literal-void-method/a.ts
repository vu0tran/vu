// this in a literal an inferring callback returns (mobx-state-tree's .actions): a method that reads
// this itself, with annotated parameters and no return value, is typed by its signature (void), as
// tsc has it once the call is resolved, not as the constraint's Function
type FunctionWithFlag = Function & { _isFlowAction?: boolean };
type ModelActions = { [key: string]: FunctionWithFlag };
interface Model<P, O> {
  actions<A extends ModelActions>(fn: (self: P & O) => A): Model<P, O & A>;
}
declare const store: Model<{ log: string[] }, {}>;
export const S = store.actions((self) => ({
  _push(entry: string) {
    self.log.push(entry);
  },
  _merge(entries: string[], opts: { all?: boolean } = {}) {
    for (const e of entries) this._push(e);
    if (opts.all) self.log.length = 0;
  },
  add(entry: string) {
    this._merge([entry]);
    const v: string = this._merge([entry], { all: true });
    this._merge(1);
    return v;
  },
}));
