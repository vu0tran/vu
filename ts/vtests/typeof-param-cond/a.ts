interface Opts { legacy?: boolean; locale?: string }
interface Box<L> { global: L extends true ? { a: number } : { b: { value: string } } }
declare function create<L extends boolean = true, O extends Opts = Opts>(o: O): (typeof o)['legacy'] extends true ? Box<true> : (typeof o)['legacy'] extends false ? Box<false> : Box<L>;
const i = create<false>({ legacy: false, locale: 'en' });
i.global.b.value = 'x';
const n: number = i.global.b.value;
