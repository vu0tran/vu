type Out<T extends unknown[]> = { [K in keyof T]: T[K] extends { o: infer O } ? O : never };
type WithRest<T extends unknown[], R = null> = R extends { o: unknown } ? [...Out<T>, ...R['o'][]] : Out<T>;
export const a: 'z' = null as unknown as WithRest<[{ o: 1 }, { o: 's' }], { o: boolean }>;
export const b: 'z' = null as unknown as WithRest<[{ o: 1 }]>;
