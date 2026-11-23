// A property's receiver from a union contextual type (an optional parameter): tsgolint skips the
// receiver check when the operand isn't assignable to the non-nullable receiver, and
// NonNullable<unknown> is {}. isPropertyInProblematicContext.
declare function f(o: Record<string, unknown>): void;
declare function f3(o?: Record<string, unknown>): void;
declare function f4(o: Record<string, unknown> | undefined): void;
function f5(o: Record<string, unknown> = {}) { return o; }
declare function f6(o: { a: unknown } | undefined): void;
declare function f7(o?: string): void;
declare const u: unknown;
f({ a: 'x' as unknown as 'y' });
f3({ a: 'x' as unknown as 'y' });
f4({ a: 'x' as unknown as 'y' });
f5({ a: 'x' as unknown as 'y' });
f6({ a: 'x' as unknown as 'y' });
f3({ a: u as 'y' });
f7('x' as string);
f5({ a: 1 as number });
type Icon = 'chevron-left' | 'chevron-right';
declare function icon(i: Icon | string): void;
declare const d: 'left' | 'right';
icon(`chevron-${d}` as Icon);
icon(`chevron-left` as Icon);
export const i1: string = `chevron-${d}` as Icon;
