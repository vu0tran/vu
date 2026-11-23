// An inference not at the top of the target (S | (() => S), as useState's) of an array of object
// literals: the array's element union is normalized (getWidenedType), so each member has the
// others' properties, optional and undefined.
declare function st<S>(x: S | (() => S)): [S, (v: S) => void];
declare function id<T>(x: T): T;

const [links] = st([{ title: 'a', href: '/a' }, { title: 'b', sub: [{ title: 'c' }] }]);
const h: number = links[0].href;
const s: number = links[1].sub;
const hrefs = links.map((l) => l.href);
const n: number = hrefs;
const b = id([{ p: 1 }, { q: 'x' }]);
const q: number = b[0].q;
