// Tagged templates; array destructuring assignment
export {};
const a = String.raw`a${1}b${'x'}`;
const n: number = a;
declare function tag(s: TemplateStringsArray, ...v: number[]): boolean;
const b: string = tag`x${1}y${'z'}`;
function destr() {
let a: string | undefined;
let b: number;
[a, b] = pair();
const x: boolean = a;
let c2: number;
let d: string;
[c2, d] = pair();
let p: number, q: number;
[p, q] = [1, 2];
[p, q] = [1, 's'];
}
declare function pair(): [string, number];
class K { m = ''; ms: string[] = []; f() { [this.m, this.ms] = this.g(); const z: number = this.m; } g(): [string, string[]] { return ['', []]; } }
