// <Comp<T> ...>: the component's signatures instantiated with the type arguments, no inference; an
// inherited constructor's base class type parameters don't count as the signature's
declare global {
  namespace JSX {
    interface Element { e: 1 }
    interface IntrinsicElements { [k: string]: any }
    interface ElementClass { render(): any }
    interface ElementAttributesProperty { props: {} }
  }
}
type Props<T> = { items: T[]; render: (t: T) => string };
function List<T>(props: Props<T>): JSX.Element { return null!; }
export const a = <List<number> items={[1, 2]} render={(n) => n.toFixed()} />;
export const b = <List<number> items={['x']} render={(n) => n.toFixed()} />;
declare class Base<P, S = {}> { constructor(props: P); props: P; state: S; render(): any }
class Box<T> extends Base<{ v: T }> {}
export const c = <Box<string> v={'s'} />;
export const d = <Box<string> v={1} />;
