declare namespace JSX {
  interface Element { readonly el: true }
  interface IntrinsicElements { div: { title?: string; children?: any } }
  interface ElementChildrenAttribute { children: {} }
}
// two generic components with the same type parameters, one defaulting to unknown, neither a
// subtype of the other: the union's combined signature, their props intersected
declare namespace A { function Root<P>(props: { open: boolean; payload?: P; a?: string; children?: any }): JSX.Element; }
declare namespace B { function Root<P = unknown>(props: { open: boolean; payload?: P; b?: string; children?: any }): JSX.Element; }
declare const m: boolean;
function F() {
  const S = m ? A : B;
  return (
    <div>
      <S.Root open={1}>x</S.Root>
      <S.Root open={true} payload={3} a="s" b="t">x</S.Root>
    </div>
  );
}
