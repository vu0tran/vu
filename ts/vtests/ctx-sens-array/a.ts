interface Base { id: string; versionId?: string; nodes: { n: number }[] }
interface WB extends Base { extra: 1 }
type CS<N> = { added: N[] };
type Rule<W extends Base = Base, N extends W['nodes'][number] = W['nodes'][number]> = (prev: W, next: W, diff: CS<N>) => boolean;
declare function group<W extends Base = Base>(ws: W[], rules: Array<Rule<W>>, skip?: Array<Rule<W>>): W[];
declare const ws: WB[];
group(ws, [() => true], [(prev, _next) => ['2'].includes(prev.versionId ?? '')]);
type Rule2<W extends Base = Base> = (prev: W, next: W) => boolean;
declare function group2<W extends Base = Base>(ws: W[], rules: Array<Rule2<W>>, skip?: Array<Rule2<W>>): W[];
group2(ws, [() => true], [(prev, _next) => ['2'].includes(prev.versionId ?? '')]);
declare function group3<W extends Base = Base>(ws: W[], skip?: Array<Rule<W>>): W[];
group3(ws, [(prev, _next) => ['2'].includes(prev.versionId ?? '')]);
export {};
