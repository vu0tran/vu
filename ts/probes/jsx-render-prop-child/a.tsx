// a render-prop child, the element's only child: its contextual type is the props' children
// (no-unsafe-return checks its returns against it)
declare global {
  namespace JSX {
    type Element = { el: true };
    interface IntrinsicElements { div: { children?: unknown } }
    interface ElementChildrenAttribute { children: {} }
  }
}
type Node = JSX.Element | string | null;
function Copy(props: { value: string; children: (s: { copied: boolean }) => Node }): JSX.Element { return <div>{props.children({ copied: true })}</div>; }
function Free(props: { children: (s: number) => any }): JSX.Element { return <div>{props.children(1)}</div>; }
declare const anyv: any;
export function A() {
  return (
    <div>
      <Copy value="x">
        {({ copied }: { copied: boolean }) => (copied ? anyv : null)}
      </Copy>
      <Free>{(n) => anyv + n}</Free>
    </div>
  );
}
