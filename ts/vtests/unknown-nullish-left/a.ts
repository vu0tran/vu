// unknown on the left of ?? or ||: {} (getNonNullableType), the union subtype-reduced (String(d.x ?? ''))
declare const d: Record<string, unknown>;
declare const u: unknown;
export const a: number = d.county ?? '';
export const b: number = u ?? 1;
export const c: number = String(d.city ?? '');
export const e: number = u || 'x';
export const f = d.x ?? 0;
export const g: number = f;
declare const uu: unknown;
if (uu ?? false) { const q: number = uu; void q; }
