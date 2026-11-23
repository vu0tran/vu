import type { Init, Sel } from './lib';

type Wrapper = { category?: Sel<'a', { event?: Sel<'x', { n: number }> | Sel<'y', { s: string }> }> | Sel<'b', { event?: Sel<'z', { b: boolean }> }> };
type WI = Init<Wrapper>;
type Cat = Extract<NonNullable<WI['category']>, { case: string }>;
type Name = Cat['case'];
type Data<C extends Name> = NonNullable<Extract<Cat, { case: C }>['value']>;
type Events<C extends Name> = NonNullable<Data<C>['event']>;
type EventName<C extends Name = Name> = NonNullable<Events<C>['case']>;
type EventData<C extends Name, E extends EventName<C>> = Extract<Events<C>, { case: E }>['value'];

type TJ = <C extends Name, E extends EventName<C>>(c: C, e: E, d: EventData<C, E>) => void;
declare const tj: TJ;
tj('a', 'x', { n: 1 });
const bad: number = tj;
