// An object with an optional discriminant to a union of intersections (MUI's Select props, as
// JSX gives them: IntrinsicAttributes & FilledSelectProps & BaseSelectProps): each value of the
// discriminant picks a member, an optional one taking a required one (propertyRelatedTo's
// skipOptional); the other properties against that member (typeRelatedToDiscriminatedType).
interface Base { fullWidth?: boolean; disabled?: boolean }
interface Attrs { key?: string }
interface Filled { variant: "filled"; hidden?: boolean }
interface Standard { variant?: "standard" }
interface Outlined { variant?: "outlined"; label?: string }
type Props = (Attrs & Filled & Base) | (Attrs & Standard & Base) | (Attrs & Outlined & Base);
declare const p: { className?: string; variant?: "filled" | "outlined" | "standard" | undefined };
export const a: Props = { ...p, fullWidth: true, disabled: true };
declare const q: { variant?: "filled" | "outlined" | "standard" | undefined; fullWidth: string };
export const b: Props = { ...q };
declare const r: { variant: "filled" | "standard"; label: number };
export const d: Props = r;
declare const s: { variant?: "outlined" | "filled" };
export const e: (Filled & Base) | (Outlined & Base) = s;
interface Base2 { variant?: "filled" | "outlined" | "standard" | undefined; fullWidth?: boolean }
type Props2 = (Attrs & Filled & Base2) | (Attrs & Standard & Base2) | (Attrs & Outlined & Base2);
export const f: Props2 = { ...p, fullWidth: true };
export const g: Props2 = { ...q };
