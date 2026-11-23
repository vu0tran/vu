// inference from a generic source signature: its type parameters at their base constraints, each through the others' (getBaseSignature), as ComponentProps<typeof DragDropProvider>
interface Data { d: 1 }
interface Box<T> { t: T }
type Props<T, U> = { on?: (t: T, u: U) => void };
declare function P<T extends Data = Data, U extends Box<T> = Box<T>>(p: Props<T, U>): null;
type CP<F> = F extends (p: infer A) => any ? A : {};
type H = NonNullable<CP<typeof P>["on"]>;
declare const h: H;
const n: number = h;
