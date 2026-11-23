// A function whose parameters are all annotated isn't context-sensitive: it keeps its own
// signature, not its generic contextual signature's type parameters (assignNonContextualParameterTypes).
type Tx<T> = <R>(t: (tx: string) => Promise<R>, config?: number) => Promise<R>;
export const g1: Tx<1> = async (w: (tx: never) => Promise<unknown>) => w(null as never);
export const g2: <R>(t: (tx: string) => Promise<R>) => Promise<R> = async (w: (tx: string) => Promise<unknown>) => w('');
export const g3: <R>(t: () => R) => R = (w: () => unknown) => w();
