interface Tool { name: string }
type Srv = Record<string, unknown>;
type Params<S, R = string> = { model: string; tools?: (Srv | Tool)[]; responseFormat?: R; state?: S };
declare function create<S = undefined, const TT extends readonly (Tool | Srv)[] = readonly (Tool | Srv)[]>(p: Omit<Params<S, never>, 'responseFormat'> & { tools?: TT }): { tools: TT };
declare const t1: Tool;
export const a = create({ model: 'x', tools: [t1] });
export const n1: number = a;
