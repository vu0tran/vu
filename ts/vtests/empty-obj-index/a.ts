// The {} that narrowing unknown gives has no implicit index signature (a type literal {} has).
function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}
export function p(usage: unknown) {
	if (usage === undefined || usage === null) return undefined;
	if (!isRecord(usage)) return 1;
	return usage.inputTokens ?? usage.promptTokens;
}
export function q(u: unknown) {
	if (typeof u === 'string') return 0;
	if (typeof u === 'number' || typeof u === 'boolean') return 1;
	if (Array.isArray(u)) return 2;
	if (isRecord(u)) { const k = Object.keys(u); return u[k[0] ?? 'k']; }
	return 3;
}
declare const u: unknown;
if (u !== undefined && u !== null) {
	const r: Record<string, unknown> = u;
	const r2: Record<string, number> = u;
	const r3: { [k: number]: string } = u;
}
const e: {} = 1;
export const r4: Record<string, unknown> = e;
