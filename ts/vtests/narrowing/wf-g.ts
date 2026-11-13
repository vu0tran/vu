type AstNode = { type: string } & Record<string, unknown>;
export function f(node: AstNode) {
  const { expressions, type } = node;
  const q: 'z' = expressions;
  const r: 'z' = type;
  const s: 'z' = node.other;
}
