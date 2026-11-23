// Under exactOptionalPropertyTypes an optional property prints without the undefined (its
// missing type isn't printed); one written with undefined keeps it.
const n1: number = null! as { a?: string };
const n2: number = null! as { a?: string | undefined; b: number };
const n3: number = null! as Partial<{ a: string; b: boolean }>;
declare const o: { a?: string };
const n4: number = o.a;
