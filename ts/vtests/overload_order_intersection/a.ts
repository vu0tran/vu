// reorderCandidates: a signature declared by another symbol goes after all those before it (its
// cutoff), so an intersection's members keep their order (express's ApplicationRequestHandler,
// IRouterHandler<T> & ((...handlers: RequestHandlerParams[]) => T)): the callback's parameters
// come from the first overload, not from the union of the last.
interface Req<P = {}> { params: P; url: string }
interface Res { send(x: string): void }
interface Next { (err?: any): void }
type Handler<P = {}> = (req: Req<P>, res: Res, next: Next) => void;
type EHandler = (err: any, req: Req, res: Res, next: Next) => void;
type Params = Handler | EHandler | Array<Handler | EHandler>;
interface H<T> {
  (...handlers: Array<Handler>): T;
  <P = {}>(...handlers: Array<Handler<P>>): T;
}
declare const h3: H<number> & ((...handlers: Params[]) => number);
h3((req, res, next) => { const n: number = next; });
type AH<T> = H<T> & ((...handlers: Params[]) => T);
declare const h4: AH<number>;
h4((req, res, next) => { const n: number = next; });
// (merged interfaces' overloads: the later declaration's first)
interface M { f(x: string): string }
interface M { f(x: 1): number }
declare const m: M;
export const r: boolean = m.f(1);
