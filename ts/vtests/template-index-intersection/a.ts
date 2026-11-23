// A template literal key on an intersection: its members' template literal index signatures that
// take it, intersected (antd's InputProps & RefAttributes through Omit<P, 'ref'>).
interface P { a: string; [k: `data-${string}`]: string | undefined }
type I = P & { ref?: 1 };
const x1: number = null! as P[`data-${string}`];
const x2: number = null! as I[`data-${string}`];
const x3: number = null! as I['data-x'];
type O = Omit<I, 'ref'>;
const x4: O = { a: '', 'data-q': 'z' };
const x5: number = x4['data-q'];
const x6: number = null! as (P & { [k: `data-${string}`]: number | undefined })[`data-${string}`];
