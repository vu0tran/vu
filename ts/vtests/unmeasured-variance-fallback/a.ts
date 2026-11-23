// Two instantiations of an interface whose type parameter's variance isn't measured (through a
// mapped type in a conditional type): a failed check of the type arguments falls back to the
// members (zod's $ZodErrorMap<$ZodIssue> to $ZodErrorMap<never>).
interface IssueBase { code: string; message?: string }
interface IssueA extends IssueBase { code: 'a' }
interface IssueB extends IssueBase { code: 'b' }
type Issue = IssueA | IssueB;
type Raw<T extends IssueBase> = T extends any ? { [K in keyof T]?: T[K] } & { extra?: unknown } : never;
type Internal<T extends IssueBase = Issue> = T extends any ? Raw<T> : never;
interface EMap<T extends IssueBase = Issue> {
  (issue: Internal<T>): string | undefined;
}
declare const m: EMap<Issue>;
const m2: EMap<never> = m;
interface D1 { error?: EMap<never> | undefined }
interface D2 { error?: EMap<Issue> | undefined }
declare const d: D2;
const d1: D1 = d;
declare const ma: EMap<IssueA>;
const mb: EMap<IssueB> = ma;
