// The contextual signature of an intersection of two function types: a parameter that is any in
// one and a ReactNode-like union in the other (related both ways, not identical) is their union,
// any (combineSignaturesOfIntersectionMembers).
type RN = string | number | { k: RN } | null | undefined;
type F = ((label: RN, p: readonly number[]) => string) & ((label: any, p: readonly number[]) => string);
const f: F = (label) => { const n: number = label; return ''; };
type G = ((label: string, p: readonly number[]) => string) & ((label: string, p: readonly number[]) => string);
const g: G = (label) => { const n: number = label; return ''; };
