// a const type parameter's option object: a property typed by a conditional on it that isn't a
// const type variable puts nothing below in a const context; an optional array property X[] |
// undefined is the array for its elements (incur's command definitions)
interface Schema<T> { _out: T }
type Out<S> = S extends Schema<infer T> ? T : never;
type Usage<O> = { options?: O extends Schema<any> ? Partial<Record<keyof Out<O>, true>> | undefined : undefined; prefix?: string };
type Def<O> = {
  options?: O;
  alias?: O extends Schema<any> ? Partial<Record<keyof Out<O>, string>> : Record<string, string> | undefined;
  usage?: Usage<O>[] | undefined;
  run(o: Out<O>): unknown;
};
declare function command<const O extends Schema<any> | undefined = undefined>(name: string, def: Def<O>): O;
declare const opts: Schema<{ template: string; phone?: string }>;
const r = command('serve', {
  options: opts,
  alias: { template: 't' },
  usage: [{ options: { template: true, phone: true } }, { prefix: 'cat |' }],
  run(o) {
    const n: number = o.template;
    return n;
  },
});
export const s: string = r;
