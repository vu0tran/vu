const parseJson = (value: unknown): Record<string, unknown> => {
  if (!value) return {};
  if (typeof value === 'object' && !Array.isArray(value)) return value as Record<string, unknown>;
  const n: number = value;
  return {};
};
const f = (raw: unknown) => {
  const hasValue = raw != null && !(typeof raw === 'string' && raw.trim() === '');
  if (hasValue) { const n: number = raw; }
  if (raw != null && !(typeof raw === 'string' && raw.trim() === '')) { const n: number = raw; }
};
const g = (raw: string | number | object) => {
  if (!(typeof raw === 'string' && raw.length > 0)) { const n: number = raw; }
};
