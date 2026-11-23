// <A.B<T> ...>: the type parameters of the signature the element resolves to.
declare global {
  namespace JSX {
    interface Element {}
    interface IntrinsicElements {}
  }
}
declare const Combobox: {
  Root: <T = string>(props: { items: T[] }) => JSX.Element;
  Plain: <T>(props: { items: T[] }) => JSX.Element;
};
export const a = <Combobox.Root<string> items={['a']} />;
export const b = <Combobox.Root<number> items={[1]} />;
export const c = <Combobox.Plain<number> items={[1]} />;
