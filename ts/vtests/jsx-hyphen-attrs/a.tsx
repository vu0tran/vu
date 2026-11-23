declare namespace JSX {
  interface Element { readonly el: true }
  interface Cls { ref?: string | ((x: number) => void) }
  interface Html { role?: string; title?: string }
  interface IntrinsicElements { div: Cls & Html; span: Html }
}
declare const r: (x: number) => void;
declare const props: Cls & Html;
interface Cls { ref?: string | ((x: number) => void) }
interface Html { role?: string; title?: string }
const a = <div data-slot="a" />;
const b = <div data-slot="a" role="x" />;
const c = <div data-slot="a" ref={r} />;
const d = <div data-slot="a" ref={r} {...props} />;
const d2 = <span data-slot="a" {...props} />;
const s1 = <span data-x="1" />;
const bad: number = <div data-slot="a" />;
