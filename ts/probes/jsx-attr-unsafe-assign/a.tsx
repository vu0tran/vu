// An attribute's value is assigned to the props type's property: Map<any, any> to a
// Map<string, number> prop reports, any[] to an optional Row[] doesn't; an any value reports
// whatever the prop is (unknown too).
declare global {
  namespace JSX {
    type Element = { el: true };
    interface IntrinsicElements { div: { children?: unknown } }
  }
}
type Row = { id: string };
function Table(props: { m: Map<string, number>; rows?: Row[]; v: unknown; w: string[]; u?: Map<string, number> }): JSX.Element {
  return <div>{props.rows?.length}</div>;
}
declare const anyv: any;
declare const anyRows: any[];
export function A() {
  const m = new Map();
  return (
    <div>
      <Table m={m} rows={anyRows} v={anyv} w={anyRows} u={m} />
      <Table m={new Map()} v={1} w={[]} />
    </div>
  );
}
