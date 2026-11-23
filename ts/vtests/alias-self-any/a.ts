// a union alias that refers to itself in a type argument but is any, a member absorbing the rest (superjson's SuperJSONValue with ClassInstance = any): any, its references too
type ClassInstance = any;
type JSONValue = string | number | JSONValue[];
type Ser = Set<SJ> | Map<SJ, SJ> | undefined | ClassInstance;
type SJ = JSONValue | Ser | SJ[];
declare const v: SJ;
const n: number = v;
declare const s: Set<SJ>;
const k: number = s;
const u: string = 1;
