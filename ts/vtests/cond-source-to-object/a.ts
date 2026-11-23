// A conditional source (apollo's VariablesOption<V>) to an object type, generic or not: only its constraints relate it; an intersection source's concrete members are tried before its generic ones.
type VariablesOption<T extends object> = {} extends T ? { variables?: T } : { variables: T };
type Params<D, V extends object> = VariablesOption<V> & { query: string; mw?: D[] };
type Props<D, V extends object> = Params<D, V> & { children: () => void };
function use<D, V extends object>(p: Params<D, V>) {}
function comp<D, V extends object>(p: Props<D, V>) {
  use<D, V>(p);
  const q: { query: string; mw?: D[] } = p;
  const r: { query: number } = p;
  const v: VariablesOption<V> = p;
  const w: { other: string } = null as unknown as VariablesOption<V>;
}
