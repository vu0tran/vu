// spreading arrays into object literals: Array's members, related to arrays
export {};
interface P { [key: string]: number }
declare const arr: P[];
const r = { ...arr };
const t4: P[] = r;
