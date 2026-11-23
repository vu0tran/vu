// An element access by string on an intersection with a mapped type over a generic key
// (T[number]): the mapped type has no members, the other members' index signatures give the type.
type EM<Key extends PropertyKey, Value> = { readonly [E in Key]: Value };
type Opts<Values extends readonly string[]> = {
  values: Values;
  descriptions: EM<Values[number], string> & Readonly<Record<string, string>>;
  counts: EM<Values[number], string> & { [n: number]: number };
};
export function f<Values extends readonly string[]>({ values, descriptions, counts }: Opts<Values>) {
  for (const value of values) {
    const b: boolean = value;
    const description = descriptions[value];
    const c: boolean = description;
  }
  const d: boolean = counts[0 as number];
}
