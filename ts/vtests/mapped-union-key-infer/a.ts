type CSSObject = { [k: string]: string | number | CSSObject | undefined };
interface Theme { spacing: number }
declare const makeStyles: <Params = void, Sub extends string = never>(params?: {
    name?: string | undefined;
} | undefined) => <RuleName extends string>(css: Record<RuleName, CSSObject> | ((theme: Theme, params: Params, classes: Record<Sub, string>) => Record<Sub | RuleName, CSSObject>)) => (params: Params) => {
    classes: Record<RuleName, string>;
};
const useTss = makeStyles<void, 'expanded'>()((theme, _params, classes) => ({
  bottom16: { marginBottom: '16px' },
  expanded: {},
  panel: { [`&.${classes.expanded}`]: { color: 'red' } },
}));
const c = useTss().classes;
const n: number = c.bottom16;
const m: number = c.nope;
declare function f<K extends string>(x: Record<'a' | K, number>): K;
const k: 'z' = f({ a: 1, b: 2 });
declare function g<K extends string, J extends string>(x: { [P in K | J]: number }): [K, J];
const kj: null = g({ a: 1 });
