// a numeric enum's object to { [s: string]: T }: its reverse mapping's number index applies to the
// string key, so T is the members' type | string (inferFromIndexTypes, membersRelatedToIndexer)
enum TabType { A, B }
const v = Object.values(TabType);
const n: number = v;
const w = Object.values(TabType).filter((x) => !isNaN(Number(x))).map((e) => e);
const m: number = w;
