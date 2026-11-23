type Message<T extends string = string> = { readonly $typeName: T };
type MessageInit<T extends Message> = T | { [P in keyof T as P extends "$unknown" ? never : P]?: P extends "$typeName" ? never : FieldInit<T[P]> };
type OneofSelectedMessage<K extends string, M extends Message> = { case: K; value: M };
type FieldInit<F> = F extends (string | number) ? F : F extends Message ? MessageInit<F> : F extends OneofSelectedMessage<infer C, infer V> ? { case: C; value: MessageInit<V> } : F;

type A = Message<"A"> & { x: number };
type B = Message<"B"> & { y: string };
type CartCat = Message<"cart"> & { event: { case: "a"; value: A } | { case: "b"; value: B } | { case: undefined; value?: undefined } };
type WebCat = Message<"web"> & { event: { case: "c"; value: A } | { case: undefined; value?: undefined } };
type WrapperMsg = Message<"W"> & { category: { case: "cart"; value: CartCat } | { case: "web"; value: WebCat } | { case: undefined; value?: undefined } };
type Wrapper = MessageInit<WrapperMsg>;

type CategoryUnion = NonNullable<Wrapper['category']>;
type CategoryCase = Extract<CategoryUnion, { case: string }>;
type CategoryName = CategoryCase['case'];
type CategoryData<C extends CategoryName> = NonNullable<Extract<CategoryCase, { case: C }>['value']>;
type CategoryEvents<C extends CategoryName> = NonNullable<CategoryData<C>['event']>;
type EventName<C extends CategoryName = CategoryName> = NonNullable<CategoryEvents<C>['case']>;
type Event<C extends CategoryName, E extends EventName<C>> = Extract<CategoryEvents<C>, { case: E }>;
type EventData<C extends CategoryName, E extends EventName<C>> = Event<C, E>['value'];
type CategoryEventMap<C extends CategoryName> = { [E in EventName<C>]?: EventData<C, E> };
type SessionCategoryFields = { [C in CategoryName]?: CategoryEventMap<C> };
const w: SessionCategoryFields = { cart: { a: { x: 1 }, b: { y: "2" } } };
const z: number = w;
export {};
