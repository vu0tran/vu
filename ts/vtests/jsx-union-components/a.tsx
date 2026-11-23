// a union of components (ComponentType<P>, Drawer | Dialog): each member's props intersected, as
// getUnionSignatures combines their signatures
declare global {
  namespace JSX {
    interface Element { e: 1 }
    interface IntrinsicElements { [k: string]: any }
    interface ElementClass { render(): any }
    interface ElementAttributesProperty { props: {} }
  }
}
declare class Cls<P> { constructor(props: P); props: P; render(): any }
type ComponentType<P> = (new (props: P) => Cls<P>) | ((props: P) => JSX.Element | null);
declare const C: ComponentType<{ a: number; b?: string }>;
export const x = <C a={1} />;
export const y = <C a={'s'} />;
declare const D1: (p: { a: number; x?: 1 }) => JSX.Element;
declare const D2: (p: { a: number; y?: 2 }) => JSX.Element;
declare const S: typeof D1 | typeof D2;
export const z = <S a={1} x={1} />;
export const w = <S a={1} y={3} />;
