// Tuples with rest, optional and labeled elements elide as other lists do (mapToTypeNodes), and
// the n-th node printed takes the n-th element's flags
declare const t1: ["compare_plan" | "compare_trading_options" | "help" | "item_sale" | "item_value" | "interest_payment" | "interest_rate" | "resource_search_url" | "resolve_address", ...("compare_plan" | "compare_trading_options" | "help" | "item_sale" | "item_value" | "interest_payment" | "interest_rate" | "resource_search_url" | "resolve_address")[]];
const n1: number = t1;
declare const t2: [{ aaaaaaaaaaaaaaaaaaaaaa: string; bbbbbbbbbbbbbbbbbbbbbbb: number; ccccccccccccccccccccc: string; dddddddddddddddddddddddd: string; eeeeeeeeeeeeeeeeeeeeeeee: string; ffffffffffffffffffffff: string }, [s: string, options?: { exact: boolean }], [string, number?], [...rest: string[]]];
const n2: number = t2;
declare const t3: [aaaaaaaaaaaaaaaaaaaa: string, bbbbbbbbbbbbbbbbbbbbbbbbb: number, cccccccccccccccccccc: string, dddddddddddddddddddddd: number, eeeeeeeeeeeeeeeeeeee: { x: string; y: number; z: boolean }, f?: string | number, ...g: ("p" | "q")[]];
const n3: number = t3;
declare const t4: [{ aaaaaaaaaaaaaaaaaaaaaa: string; bbbbbbbbbbbbbbbbbbbbbbb: number; ccccccccccccccccccccc: string }, { aaaaaaaaaaaaaaaaaaaaaa: string; bbbbbbbbbbbbbbbbbbbbbbb: number; ccccccccccccccccccccc: string }, string, number, boolean, string, number?, ...(string | number)[]];
const n4: number = t4;
declare const t5: readonly [string, number?, ...(readonly string[])[]];
const n5: number = t5;
declare const t6: [{ aaaaaaaaaaaaaaaaaaaaaa: string; bbbbbbbbbbbbbbbbbbbbbbb: number; ccccccccccccccccccccc: string; dddddddddddddddddddddddd: string; eeeeeeeeeeeeeeeeeeeeeeee: string; ffffffffffffffffffffff: string }, number?, ...(string | number)[]];
const n6: number = t6;
