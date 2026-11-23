// exactOptionalPropertyTypes: an optional property prints without the missing undefined
type Case = { id: string };
declare const r: { negatives?: Case[]; stats?: unknown; n?: number | undefined };
const x: number = r;
const y: string = { a: 1 } as { a?: number };
