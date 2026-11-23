// (skipLibCheck: a declaration file is not checked, its type arguments' constraints neither)
type Str<T extends string> = { s: T };
type Strs<K> = { [P in keyof K]: Str<K[P]> };
declare const env: Strs<{ a: "x" }>;
