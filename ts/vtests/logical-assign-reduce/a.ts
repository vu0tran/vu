interface Node1 { readonly value: unknown; children?: Map<string, Node1> }
export class R {
  private root?: Node1;
  get(): Node1 { let node = (this.root ??= { value: 1 }); return node.children?.get('x') ?? node; }
  get2(): Node1 { let n2 = (this.root ||= { value: 2 }); void n2.children; return n2; }
}
let x: string | undefined;
export const y = (x ??= "a");
let z: { a: number } | null = null;
export const w = (z ||= { a: 1 });
