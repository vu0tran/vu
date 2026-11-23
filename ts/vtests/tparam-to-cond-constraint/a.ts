// A type parameter to a conditional type: through its constraint (TName extends FieldPath<T> to Path<T>); a target depending on the distribution has no other rule.
type PathI<T> = { [K in keyof T]: K }[keyof T];
type Path<T> = T extends any ? PathI<T> : never;
type FieldPath<T> = Path<T>;
function reg<T, N extends Path<T>>(n: N) {}
function f<TF extends { a: string }, TN extends FieldPath<TF>>(name: TN) {
  reg<TF, TN>(name);
  const p: Path<TF> = name;
}
function g<TF, TN extends string>(name: TN) {
  const p: Path<TF> = name;
}
