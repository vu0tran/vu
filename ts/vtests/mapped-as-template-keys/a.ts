// (hono's MergeSchemaPath: an as clause naming a property by a pattern template literal, a
// template literal index signature; over those keys again, their names; keyof, the names)
type MergePath<A extends string, B extends string> = B extends '' ? MergePath<A, '/'> : A extends '' ? B : A extends '/' ? B : A extends `${infer P}/` ? B extends `/${infer Q}` ? `${P}/${Q}` : `${P}/${B}` : B extends `/${infer Q}` ? Q extends '' ? A : `${A}/${Q}` : `${A}/${B}`;
type Endpoint = { input: any; output: any };
type Schema = { [Path: string]: { [Method: `$${Lowercase<string>}`]: Endpoint } };
type MergeSchemaPath<OrigSchema extends Schema, SubPath extends string> = {
  [P in keyof OrigSchema as MergePath<SubPath, P & string>]: { [M in keyof OrigSchema[P]]: OrigSchema[P][M] };
};
type S0 = { "/a": { $get: { input: {}; output: { a: 1 } } }; "/b": { $post: { input: {}; output: { b: 2 } } } };
type S1 = MergeSchemaPath<S0, string>;
type S2 = MergeSchemaPath<S1, "/api">;
type S3 = MergeSchemaPath<S1, string>;
declare const s2: S2;
declare const s3: S3;
const x1: number = s2["/api/x/a"];
const x2: number = s3["q/a"];
const x3: string = s2["/api/x/b"].$post.output;
declare const k1: keyof S1;
const y1: number = k1;
declare const k2: keyof S2;
const y2: number = k2;
declare const s1: S1;
const y3: number = s1;
const y4: number = s1["q/a"];
export {};
