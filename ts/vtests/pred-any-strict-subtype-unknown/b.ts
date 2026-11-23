interface El<P = any> { type: string; props: P }
interface Portal extends El { children: string }
type Node = El | string | number | Portal | null | undefined;
declare function isEl<P>(o: {} | null | undefined): o is El<P>;
declare const n: Node;
export function f() {
  if (isEl(n)) {
    const x: [typeof n] = 0;
    const y: [typeof n.props] = 0;
  }
}
declare function isRec(value: unknown): value is Record<string, unknown>;
declare const d2: Record<string, any> | null;
declare const d3: { a: any } | null;
declare function isA(value: unknown): value is { a: unknown };
export function g() {
  if (isRec(d2)) { const p: [typeof d2] = 0; }
  if (isA(d3)) { const p: [typeof d3] = 0; }
}
