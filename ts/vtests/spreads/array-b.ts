// spreading arrays into object literals: Array's members, related to arrays
export {};
interface P { [key: string]: V }
type V = string | number | P | P[];
declare const arr: P[];
const r = { __rl: true, ...arr };
const t4: P[] = r;
