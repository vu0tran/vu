export type DeferredToolResolver = 'client' | string;
export interface DeferredTool<TInput = unknown, TResult = unknown, TName extends string = string, TResolver extends DeferredToolResolver = DeferredToolResolver> {
  kind: 'deferred'; name: TName; input: TInput; r?: TResult; resolver: TResolver;
}
export type DeferredToolCall<TArguments = unknown, TName extends string = string, TResolver extends DeferredToolResolver = DeferredToolResolver> = {
  id: string; name: TName; arguments: TArguments; resolver: TResolver;
};
export type DeferredToolCallForTool<TTool> =
  TTool extends DeferredTool<infer TInput, unknown, infer TName, infer TResolver>
    ? DeferredToolCall<TInput, TName, TResolver>
    : never;
export type DeferredToolCallUnion<TDeferredTools extends readonly DeferredTool[]> =
  DeferredToolCallForTool<TDeferredTools[number]>;
export type PendingDeferredToolCall = { id: string; name: string; arguments: unknown; resolver: DeferredToolResolver };
export type Opts<T extends readonly DeferredTool[]> = { tools: T; pend?: { calls: PendingDeferredToolCall[] } };
