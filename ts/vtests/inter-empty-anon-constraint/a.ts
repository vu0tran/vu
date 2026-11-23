// A type parameter whose constraint is NonNullable<X['case']> (X['case'] & {}), related to string:
// the intersection's effective constraint, {} being a disjoint domain type
// (getEffectiveConstraintOfIntersection's isEmptyAnonymousObjectType).
type U =
  | { case: 'a'; value: { event?: { case: 'x'; value: number } | { case: undefined; value?: undefined } } }
  | { case: 'b'; value: { event?: { case: 'z'; value: boolean } | { case: undefined; value?: undefined } } }
  | { case: undefined; value?: undefined };
type Case = Extract<U, { case: string }>;
type Name = Case['case'];
type Data<C extends Name> = NonNullable<Extract<Case, { case: C }>['value']>;
type Events<C extends Name> = NonNullable<Data<C>['event']>;
type EventName<C extends Name> = NonNullable<Events<C>['case']>;
export function f<C extends Name, E extends EventName<C>, H extends NonNullable<Events<C>['case']>>(e: E, h: H) {
  const a: string = e;
  const b: string = h;
  const o = { [e]: 1 };
  const d: boolean = o.k;
}
