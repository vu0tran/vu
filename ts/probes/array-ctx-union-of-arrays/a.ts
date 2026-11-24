export enum Job {
  Call = 'call',
  Text = 'text',
}
export enum Form {
  Access = 'access',
}
export enum Col {
  One = 'one',
  Two = 'two',
}

interface Each {
  <T extends readonly [any, ...any[]]>(cases: ReadonlyArray<T>): (name: string, fn: (...args: T) => void) => void;
  <T extends any[] | [any]>(cases: ReadonlyArray<T>): (name: string, fn: (...args: T) => void) => void;
  <T>(cases: ReadonlyArray<T>): (name: string, fn: (...args: T[]) => void) => void;
}
declare const each: Each;
declare function pick(xs: readonly string[]): Col[] | null;

each([
  ['first', [Job.Call], [Col.One]],
  ['second', [Job.Call, Job.Text], [Col.One, Col.Two]],
  ['third', [Job.Text, Form.Access], []],
  ['fourth', [Job.Call, 'gone'], null],
])('case %s', (_name, sel, want) => {
  void pick(sel);
  void want;
});

declare function each2<T extends any[] | [any]>(cases: ReadonlyArray<T>): (fn: (...args: T) => void) => void;
each2([
  ['a', [Job.Call]],
  ['b', [Job.Call, 'gone']],
])((n, s) => {
  void n;
  void s;
});
