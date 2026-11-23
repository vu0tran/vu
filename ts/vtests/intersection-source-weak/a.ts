// An intersection source related to a member of an intersection target: each of the source's
// members is tried with the weak type check on (IntersectionState.Source), so a member without the
// target's properties doesn't fit a target whose properties are all optional.
interface Label { l: number }
interface Anchor { a: string }
interface ClassAttributes<T> { ref?: { current: T | null } }
type Props = { color?: string; children?: string } & { ref?: { current: Label | null } } & { component?: string };
declare const p: Props;
const x1: ClassAttributes<Anchor> & { title?: string } = p;
type Fits<K> = Props extends ClassAttributes<K> & { title?: string } ? 1 : 0;
const x2: Fits<Anchor> = 1;
const x3: Fits<Label> = 0;
const x4: ClassAttributes<Label> & { title?: string } = p;
