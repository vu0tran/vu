type R = 'default' | 'junit' | (string & {});
type Arrayable<T> = T | T[];
declare function cfg(o: { reporters?: Arrayable<R | [R, object]> }): void;
cfg({ reporters: ['default', 'junit'] });
cfg({ reporters: process_ok() ? ['default'] : ['x'] });
declare function process_ok(): boolean;
declare function cfg2(o: { r: string & {} }): void;
cfg2({ r: ['a'] });
