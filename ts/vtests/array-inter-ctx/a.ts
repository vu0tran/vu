type AllowWarnDeny = ("allow" | "off" | "warn" | "error" | "deny") | number;
type RuleNoConfig = AllowWarnDeny | [AllowWarnDeny];
interface CC { max?: number }
type ComplexityConfigEnum = number | CC;
interface Rules { complexity?: RuleNoConfig | [AllowWarnDeny, ComplexityConfigEnum]; other?: RuleNoConfig }
interface Cfg { rules?: Rules; extends?: Cfg[] }
declare function defineConfig<T extends Cfg>(config: T & Cfg): T;
export default defineConfig({ rules: { complexity: ['error', 23], other: 'off' } });
export const two = defineConfig({ extends: [], rules: { other: ['warn'] } });
declare function both<T>(x: T & { xs: (1 | 2)[] }): T;
export const three = both({ xs: [1, 2] });
interface A1 { a: number[] } interface B1 { a: (1 | 2 | 3)[] }
declare function inter(x: A1 & B1): void;
inter({ a: [1, 2] });
declare function tup(x: ["a" | "b", number] & [string, 1 | 2]): void;
tup(["a", 2]);
