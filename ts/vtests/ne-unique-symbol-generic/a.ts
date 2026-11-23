// x !== S (a unique symbol) where x has generic members: they aren't unit types, so they stay
declare const skipToken: unique symbol;
type SkipToken = typeof skipToken;
type OperationVariables = Record<string, any>;
type EmptyObject = Record<string, never>;
type OptionalVars<TOptions extends object | SkipToken, TVariables extends OperationVariables = EmptyObject> =
  EmptyObject extends TVariables ? [param?: TOptions | undefined] : [param: TOptions];
type VariablesOption<TVariables extends OperationVariables> = {} extends TVariables ? { variables?: TVariables } : { variables: TVariables };
type Options<TData, TVariables extends OperationVariables> = { context?: { a?: number }; data?: TData } & VariablesOption<NoInfer<TVariables>>;
type Authenticated = { authenticated?: boolean };
type QueryOptions<TData, TVariables extends OperationVariables> = (Options<TData, TVariables> & Authenticated) | SkipToken;

export function useQuery<TData = unknown, TVariables extends OperationVariables = EmptyObject>(
  q: TData,
  ...[options]: OptionalVars<QueryOptions<TData, TVariables>, TVariables>
) {
  const authenticated = options !== skipToken && options?.authenticated;
  const resolvedOptions = options === skipToken ? undefined : options;
  const ctx = { ...resolvedOptions?.context, b: 1 };
  const c2: number = ctx;
  const a2: number = authenticated;
  return authenticated;
}

// (and a const of it: its declared type's members the initializer may be assigned to, the
// intersection related through its conditional member's union constraint)
export function g2<TData = unknown, TVariables extends OperationVariables = EmptyObject>(
  o: (Options<TData, TVariables> & Authenticated) | undefined,
) {
  const r = o;
  const q = r?.context;
  const w: string = q;
  const v: number = r?.variables;
}
