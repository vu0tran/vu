// Generic aliases over a protobuf-style oneof (observability's CategoryEvents<C>): one copy of each
// alias instantiation by two paths, NonNullable<X[K]> by X's base constraint, E by its constraint
type Ev1 = { case: 'x'; value: { n: number } } | { case: 'y'; value: { s: string } } | { case: undefined; value?: undefined };
type Ev2 = { case: 'z'; value: { b: boolean } } | { case: undefined; value?: undefined };
type Init = { category?: { case: 'a'; value: { event?: Ev1 } } | { case: 'b'; value: { event?: Ev2 } } | { case: undefined; value?: undefined } };
type CategoryUnion = NonNullable<Init['category']>;
type CategoryCase = Extract<CategoryUnion, { case: string }>;
type CategoryName = CategoryCase['case'];
type CategoryData<C extends CategoryName> = NonNullable<Extract<CategoryCase, { case: C }>['value']>;
type CategoryEvents<C extends CategoryName> = NonNullable<CategoryData<C>['event']>;
type EventName<C extends CategoryName = CategoryName> = NonNullable<CategoryEvents<C>['case']>;
type EventData<C extends CategoryName, E extends EventName<C>> = Extract<CategoryEvents<C>, { case: E }>['value'];
type TrackSessionEvent = <C extends CategoryName, E extends EventName<C>>(categoryName: C, eventName: E, eventData: EventData<C, E>) => void;
type TrackError = (label: string, error?: Error) => void;
declare const te: TrackError;
const a: TrackSessionEvent = te;
declare function pick(f: TrackSessionEvent | TrackError): void;
pick(te);
