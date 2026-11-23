// an array literal whose contextual type intersects Iterable<T> with an object type without a
// number index (React's Iterable<ReactNode> & ReactElement): its elements get T
interface El { type: string; props: unknown }
type RNode = string | number | El | Iterable<RNode> & El | null;
declare function take(x: RNode): void;
take([1, 'a', (y) => y]);
declare function take2(x: Iterable<(n: number) => void> & { tag: string }): void;
take2([(n) => { const s: string = n; }]);
