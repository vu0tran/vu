declare namespace JSX {
  interface Element { readonly el: true }
  interface IntrinsicElements { div: { title?: string; onClick?: () => void }; b: {} }
  interface ElementChildrenAttribute { children: {} }
}
type Node = JSX.Element | string | number;

function List<T>(props: { items: T[]; render: (t: T) => Node }) { return <div />; }
function Pair<A, B>(p: { a: A } & { b: B; f: (a: A, b: B) => void }) { return <div />; }

const ok1 = <List items={[1, 2, 3]} render={(x) => x.toFixed(1)} />;
const bad1 = <List items={[1, 2, 3]} render={(x) => x.toUpperCase()} />;
const ok2 = <Pair a="s" b={1} f={(x, y) => { x.charAt(0); y.toFixed(); }} />;
const bad2: number = <div title="t" />;
const bad3 = <div title={1} />;
const bad4 = <List items={["a"]} render={(x: number) => x} />;
const bad5 = <div foo="x" />;
const bad6 = <b>{1}</b>;
function Btn(p: { label: string; n?: number }) { return <div />; }
const c1 = <Btn label="x" foo={1} />;
const c2 = <Btn n={1} />;
const c3 = <Btn label={2} />;
const c4 = <Btn label="ok" n={3} />;
class K { props!: { k: string }; render() { return <div />; } }
const c5 = <K k={1} />;
const c6 = <Nope />;
