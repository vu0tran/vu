// An interface declared before a class of the same name merges into it (heritage too)
interface Base { off(): number; }
interface EE extends Base {}
class EE { emit(): boolean { return true; } }
declare const e: EE;
const n1: number = e.off();
const n2: string = e.emit();
// Pick over an intersection keeps optionality
type R = { shouldReport?: boolean; level?: 'a' | 'b' };
type B2 = { description?: string } & R;
type O2 = Omit<B2, 'level'> & { level?: 'a' };
const o: O2 = { level: 'a', shouldReport: true };
const o2: O2 = { level: 'b' };
