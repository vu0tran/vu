type DeferredToolResolver = 'client' | string;
interface DeferredTool<TInput = unknown, TResult = unknown, TName extends string = string, TResolver extends DeferredToolResolver = DeferredToolResolver> {
  kind: 'deferred'; name: TName; input: TInput; r?: TResult; resolver: TResolver;
}
type DeferredToolCall<TArguments = unknown, TName extends string = string, TResolver extends DeferredToolResolver = DeferredToolResolver> = {
  id: string; name: TName; arguments: TArguments; resolver: TResolver;
};
type DeferredToolCallForTool<TTool> =
  TTool extends DeferredTool<infer TInput, unknown, infer TName, infer TResolver>
    ? DeferredToolCall<TInput, TName, TResolver>
    : never;
type DeferredToolCallUnion<TDeferredTools extends readonly DeferredTool[]> =
  DeferredToolCallForTool<TDeferredTools[number]>;
type PendingDeferredToolCall = { id: string; name: string; arguments: unknown; resolver: DeferredToolResolver };
class H<const TD extends readonly DeferredTool[], TC = unknown> {
  constructor({ m, ctx }: { m: Map<string, TD[number]>; ctx?: TC }) {}
  restore({ calls }: { calls: DeferredToolCallUnion<TD>[] }): void {}
}
function f<const T extends readonly DeferredTool[]>(tools: T, pend: PendingDeferredToolCall[]) {
  const m = new Map<string, T[number]>(tools.map((t) => [t.name, t]));
  const h = new H({ m });
  const n: number = h;
  h.restore({ calls: pend });
}
