// Two generic template literal types (hono's `${MergePath<A, P>}/${P}`): the same texts relate placeholder by placeholder; a leading or trailing text that can't match isn't related.
type MergePath<A extends string, B extends string> = B extends '' ? MergePath<A, '/'> : A extends '' ? B : A extends '/' ? B : A extends `${infer P}/` ? B extends `/${infer Q}` ? `${P}/${Q}` : `${P}/${B}` : B extends `/${infer Q}` ? Q extends '' ? A : `${A}/${Q}` : `${A}/${B}`;
function f<P extends string, Q extends string>(a: `${MergePath<"/", P>}/${P}`, b: `${P}-x`, c: `a${P}`) {
  const x: `${MergePath<any, P>}/${P}` = a;
  const y: `${string}/${P}` = a;
  const z: `${Q}-x` = b;
  const w: `a${string}` = c;
  const v: `b${P}` = c;
}
