// a context-sensitive argument for a type parameter of a method seen through an instantiation
// (setup(...).createMachine(config)): the first pass reads the constraint instantiated, as the
// signature's parameter types are, so a call in a property gets the outer type arguments
type DoNotInfer<T> = [T][T extends any ? 0 : any];
type Act<C> = (a: { context: C }) => void;
declare function assign<C>(f: (a: { context: C }) => Partial<C>): Act<C>;
interface Config<C> {
  context?: C | ((a: { input: number }) => C);
  on?: { [k: string]: { actions?: Act<DoNotInfer<C>> } };
}
interface Setup<C> {
  createMachine<const T extends Config<C>>(config: T): T;
}
declare function setup<C>(o: { types: { context: C } }): Setup<C>;
const m = setup({ types: { context: {} as { n: number; s: string } } }).createMachine({
  context: ({ input }) => ({ n: input, s: '' }),
  on: { INC: { actions: assign(({ context }) => ({ n: context.n + 1 })) } },
});
const x: number = m.on.INC;
