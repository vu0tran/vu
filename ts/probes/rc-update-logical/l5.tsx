export function A(props: { groups: { n: number }[] }) {
  props.groups ||= [];
  return <div>{props.groups.length}</div>;
}
