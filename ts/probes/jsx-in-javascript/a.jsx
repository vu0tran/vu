// JSX in a JavaScript file: read with JSX and typed as in a .tsx file
const data = JSON.parse('{}');
export function View() {
  return <div title={data.title}>{data.body.text}</div>;
}
export async function load() {
  await 1;
  return <span>{String(data.x)}</span>;
}
