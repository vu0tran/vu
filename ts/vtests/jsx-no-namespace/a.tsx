// no JSX namespace (no React types): elements are the error type, intrinsic ones TS7026 at both tags

function Comp(props: { a: number }) {
  return <div className="x">{props.a}</div>;
}
export const e = <Comp a={1} />;
export const n: number = e;
export const f = <span>hi</span>;
export function g(x: unknown) {
  return <Comp a={x as number}><b /></Comp>;
}
