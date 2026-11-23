// a computed key's receiver is its expression's type, never the contextual type
import { TaskType } from '@gql';
enum E { A = 'a', B = 'b' }
declare const k: string;
declare const anyv: any;
export const m1: { [x in E]: TaskType } = { [E.A]: TaskType.X, [E.B]: anyv };
export const m2: Record<string, unknown> = { [k]: anyv, ['lit']: anyv, plain: anyv };
export const m3: { [x: string]: unknown } = { [k]: anyv };
export const m4 = { [k]: anyv };
export const m5: Set<unknown>[] = [];
export const m6: { [x: string]: Set<unknown> } = { [k]: new Set<any>(), a: new Set<any>() };
