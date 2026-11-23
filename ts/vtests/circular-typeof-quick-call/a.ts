// a variable read while its initializer is checked, the initializer a call of a single
// non-generic signature: that signature's return, without the arguments (getQuickTypeOfExpression;
// zod's schema = z.object(...).superRefine(validate), validate taking z.infer<typeof schema>)
interface Ctx { addIssue(m: string): void }
interface Obj<T> {
  _output: T;
  superRefine(fn: (arg: T, ctx: Ctx) => void): this;
}
declare function object<T>(shape: T): Obj<T>;
type Infer<S extends { _output: unknown }> = S['_output'];
export const schema = object({ a: 1, b: 'x' }).superRefine(validate);
type Input = Infer<typeof schema>;
function validate(input: Input, ctx: Ctx): void {
  const n: string = input.a;
  inner(input, ctx);
}
function inner(input: Input, ctx: Ctx): void {
  const m: number = input.b;
}
export const schema3 = object({ a: 1 }).superRefine(validate3);
function validate3(input: string, ctx: Ctx): void {}
