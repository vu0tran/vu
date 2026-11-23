// namespace A.B { }: B is an exported namespace of A, merged with a class or a namespace B
// that other declarations give A.
function get(): typeof g.maps {
  if (typeof g === 'undefined' || !g.maps) {
    throw new Error('x');
  }
  return g.maps;
}
const maps = get();
const d = new maps.Data({ map: 1 });
const s: number = d.add();
const o: g.maps.Data.DataOptions = { map: 'x' };
const v: string = g.ui.version;
const q: number = g.ui.more.make().q;
const r: g.ui.more.Q = { q: true };
let bad: g.maps.Data.Nope;
let bad2: g.ui.more.Nope;
export {};
