// A concrete source to a conditional type with infer declarations, or whose branches depend on the distribution (swr's Fetcher<Data, SWRKey>): no rule relates them.
type FetcherResponse<D> = D | Promise<D>;
type BareFetcher<D> = (...args: any[]) => FetcherResponse<D>;
type Fetcher<D, K> = K extends () => infer A | null | false ? (arg: A) => FetcherResponse<D> : K extends null | false ? never : K extends infer A ? (arg: A) => FetcherResponse<D> : never;
type Dist<T> = T extends string ? { s: T } : { n: T };
function f<D, K, T>(b: BareFetcher<any>, o: { a: 1 }) {
  const x: Fetcher<D, K> = b;
  const y: Dist<T> = o;
  const z: Fetcher<D, K> | BareFetcher<any> = b;
}
