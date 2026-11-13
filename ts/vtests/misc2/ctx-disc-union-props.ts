interface Opt { name: string; value: string; dis?: undefined }
interface Prop { name: string; type: 'string' | 'x'; dis?: { a: 1 }; options?: Array<Opt | Prop | Coll> }
interface Coll { name: string; values: Prop[] }
export const a: Array<Opt | Prop | Coll> = [{ name: 't', values: [{ name: 's', type: 'string' }] }];
type U = { k?: 'a'; x: 1 } | { k?: 'b'; y: 1 } | { z: 1 };
export const u: U = { x: 1 };
