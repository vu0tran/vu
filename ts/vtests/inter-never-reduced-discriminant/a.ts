// an intersection whose discriminant properties conflict ('active' & 'done') is never, left out of
// a union where a property is read (getReducedType's isNeverReducedProperty; xstate's OutputFrom)
type Snap<O> =
  | { status: 'active'; output: undefined; error: undefined }
  | { status: 'done'; output: O; error: undefined }
  | { status: 'error'; output: undefined; error: unknown };
type PS<O, I> = Snap<O> & { input: I | undefined };
type B = (PS<{ k: 1 }, string> & { status: 'done' })['output'];
const b: number = null as unknown as B;
type C = (Snap<{ k: 1 }> & { status: 'done' })['output'];
const c2: number = null as unknown as C;
declare const s: Snap<{ k: 1 }> & { status: 'done' };
const o: number = s.output;
declare const t: ({ a: 1; x: string } & { a: 2 }) | { a: 3; x: number };
const tx: boolean = t.x;
