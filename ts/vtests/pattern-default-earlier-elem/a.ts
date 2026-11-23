// A destructuring element's default that reads an earlier element of the same pattern sees that
// element's type, not any (the pattern is being bound, not circular).
type Requests = { id: string }[];
export function f({
  requests = [],
  requestCount = requests.length,
}: {
  requests?: Requests;
  requestCount?: number;
} = {}) {
  const n: string = requests;
  const m: string = requestCount;
}
export function g({ a = 'x', b = a.length, c = b > 1 }: { a?: string; b?: number; c?: boolean }) {
  const p: string = c;
}
declare const src: { x?: number; y?: string };
const { x = 1, y = x.toFixed() } = src;
const q: number = y;
const [h = 2, i = h + 1] = [] as number[];
const r: string = i;
