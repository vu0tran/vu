import type { DeferredTool, DeferredToolCallUnion, Opts } from './t';
function f<const T extends readonly DeferredTool[]>(o: Opts<T>) {
  if (o.pend) {
    const x = o.pend.calls as DeferredToolCallUnion<T>[];
    const y: number = x;
    const z: number = o.pend.calls as DeferredToolCallUnion<T>[];
  }
}
