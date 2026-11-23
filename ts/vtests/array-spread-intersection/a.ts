// a spread in an array literal of an intersection with one iterable member (mobx-state-tree's
// readonly X[] & IStateTreeNode): its elements
interface Node { readonly $node?: [unknown] }
declare const keys: readonly ('a' | 'b')[] & Node;
declare const more: string[] & { tag: 1 };
export const a: number = [...keys];
export const b = [...keys, ...more];
export const c: number = b;
declare const maybe: typeof keys | undefined;
export const d: number = [...(more || []), ...(maybe ?? [])];
