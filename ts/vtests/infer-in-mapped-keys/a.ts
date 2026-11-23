// infer inside a mapped type over literal keys or a key type parameter (Hono's InputToDataByTarget)
type A1<T> = T extends { [K in 'param']: unknown } ? 1 : 2;
export const a1: A1<{ param: { id: string } }> = 3;
type A2<T> = T extends { [K in 'param']: infer R } ? 1 : 2;
export const a2: A2<{ param: { id: string } }> = 3;
type A3<T> = T extends { [K in 'param' | 'x']: infer R } ? R : 2;
export const a3: A3<{ param: { id: string }, x: 1 }> = 3;
type A<T> = T extends { [K in 'param']: infer R } ? R : never;
type C<T, Tg extends string> = T extends { [K in Tg]: infer R } ? R : never;
export const a: A<{ param: { id: string } }> = 1;
export const c: C<{ param: { id: string } }, 'param'> = 1;
