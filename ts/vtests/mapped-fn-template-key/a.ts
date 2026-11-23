// A mapped type in a non-generic alias whose template is a function type mentioning the key (user-event's UserEvent): each property instantiates it with its key.
declare const api: { click: (el: Element) => Promise<void> };
type Api = typeof api;
type Api2 = { click: (el: Element) => Promise<void> };
type U1 = { [k in keyof Api]: ReturnType<Api[k]> };
type U3 = { [k in keyof Api2]: ReturnType<Api2[k]> };
type U4 = { [k in keyof Api2]: () => ReturnType<Api2[k]> };
declare const u1: U1; declare const u3: U3; declare const u4: U4;
const n1: number = u1.click;
const n3: number = u3.click;
const n4: number = u4.click;
declare const api2: { click: (el: Element) => Promise<void> };
type ApiB = typeof api2;
type V1 = { readonly [k in keyof ApiB]: (...args: Parameters<Api[k]>) => ReturnType<Api[k]> };
type V2 = { s: 1 } & V1;
declare const v1: V1;
declare const v2: V2;
const m1: number = v1.click;
const m2: number = v2.click;
