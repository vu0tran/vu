export type JsonValue = string | number | boolean | null | JsonObject | JsonValue[];
export type JsonObject = { [key: string]: JsonValue };
function hasBody(value: unknown): value is { body: unknown } { return typeof value === 'object' && value !== null && 'body' in value; }
declare function enc<T>(r: T): T;
export function to(value: unknown): JsonValue {
	if (!hasBody(value)) return value as JsonValue;
	const a = enc({ ...value }) as JsonValue;
	const b = value as JsonValue;
	const c = { body: 1 as unknown } as JsonValue;
	const d = { body: 1 as unknown } as JsonObject;
	return value as JsonValue;
}
