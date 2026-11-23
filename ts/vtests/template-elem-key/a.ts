type ScalarField = { kind: 'bool' | 'number' | 'string' | 'strings' };
type EnumField = { kind: 'enum' | 'enums'; values: readonly string[] };
type CatalogFactField = ScalarField | EnumField;
type CatalogFactGroup = { name: string; fields: Record<string, CatalogFactField> };
type CatalogFactFieldValue<F extends CatalogFactField> = F extends { kind: 'enum'; values: readonly (infer V)[] }
  ? V
  : F extends { kind: 'number' } ? number : string[];
type CatalogFactGroupValues<G extends CatalogFactGroup> = {
  [K in keyof G['fields']]: CatalogFactFieldValue<G['fields'][K]> | undefined;
};
const defineCatalogFactGroup = <const G extends CatalogFactGroup>(group: G): G => group;
declare const readCatalogFactGroup: <G extends CatalogFactGroup>(group: G) => CatalogFactGroupValues<G>;

const ROOM_SET = defineCatalogFactGroup({
  name: 'roomSet',
  fields: {
    A_STATE: { kind: 'enum', values: ['EXACT', 'UNRESOLVED'] },
    A_MAIN: { kind: 'number' },
    B_STATE: { kind: 'enum', values: ['EXACT', 'UNRESOLVED'] },
    B_MAIN: { kind: 'number' },
  },
});
const readRoomSet = () => readCatalogFactGroup(ROOM_SET);
type Facts = ReturnType<typeof readRoomSet>;
type Kind = 'A' | 'B';

function f(facts: Facts, prefix: Kind) {
  const state = facts[`${prefix}_STATE`];
  const s: number = state;
  const m = facts[`${prefix}_MAIN`];
  const t: string = m;
}
