// a union alias with a member that is any (superjson's SuperJSONValue, through SerializableJSONValue):
// any, also for what refers to it while it is made
type ClassInstance = any;
type Serializable = Set<Value> | Date | ClassInstance;
type Value = string | Serializable | ValueArray;
interface ValueArray extends Array<Value> {}
declare const v: Value;
declare const a: ValueArray;
const n: number = v;
const m: number = a[0];
const s: string = a;
