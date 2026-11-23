// A mapped type with an as clause over a union of objects (graphql's KindVisitor): one property
// per member, named by its kind; a visitor method's parameter is that member.
declare enum Kind { FIELD = 'Field', NAME = 'Name' }
interface NameNode { readonly kind: Kind.NAME; readonly value: string }
interface FieldNode { readonly kind: Kind.FIELD; readonly name: NameNode }
type ASTNode = NameNode | FieldNode;
type ASTVisitor = EnterLeaveVisitor<ASTNode> | KindVisitor;
type KindVisitor = {
  readonly [NodeT in ASTNode as NodeT['kind']]?:
    | ASTVisitFn<NodeT>
    | EnterLeaveVisitor<NodeT>;
};
interface EnterLeaveVisitor<TVisitedNode extends ASTNode> {
  readonly enter?: ASTVisitFn<TVisitedNode>;
  readonly leave?: ASTVisitFn<TVisitedNode>;
}
type ASTVisitFn<TVisitedNode extends ASTNode> = (node: TVisitedNode, key: string | number | undefined) => any;
declare function visit<N extends ASTNode>(root: N, visitor: ASTVisitor): N;
declare const f: FieldNode;
visit(f, {
  Field(node) {
    const n: number = node.name.value;
    return undefined;
  },
});
const k: KindVisitor = { Name: (node) => { const m: number = node.value; } };
type K1 = { [N in ASTNode as N['kind']]: (n: N) => void };
const a: K1 = 1;
type K2 = { [N in ASTNode as N['kind']]?: (n: N) => void };
const b: K2 = 1;
const k1: K1 = { Name: (node) => { const m: number = node.value; }, Field: (node) => {} };
declare const kk: K1;
const z: number = kk.Name;
