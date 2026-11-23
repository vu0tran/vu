declare const anyv: any;
const fn = new Function('doc', 'body');
export const r1 = fn(anyv);
export const r2 = new Function('Cu', 'x')(anyv);
const s1 = Symbol.for(anyv);
const s2 = Symbol(anyv);
export { s1, s2 };
const rooms: any = {};
for (let i = 0; i < Object.keys(rooms).length; i++) {
  if (Object.keys(rooms)[i] == 'den') {}
}
declare const f2: Function;
f2(anyv);
