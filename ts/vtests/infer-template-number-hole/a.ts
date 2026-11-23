declare function num<P extends number>(x: `${P}`): P;
declare const tn: `${number}`;
const f: string = num(tn);
declare function two<P extends number>(x: `a${P}` | `b${P}`): P;
declare const tb: `b${number}`;
const g: string = two(tb);
export { f, g };
