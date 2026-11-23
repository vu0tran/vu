// an object literal argument to a generic call: its properties' contextual types are the
// parameter's instantiated with what the call's contextual type infers (returnMapper), so their
// literals stay where those have literals
export {};
type R = { role: 'assistant' | 'user' };
type Completion = { metadata: {}; message: { role: 'assistant' | 'user'; content: string } };
declare function id<T>(x: T): Promise<T>;
declare function id2<T>(x: T): T;
const h: Promise<R> = id({ role: 'assistant' });
const h2: Promise<{ m: R }> = id({ m: { role: 'assistant' } });
const h3: { m: R } = id2({ m: { role: 'assistant' } });
const g: Promise<Completion> = Promise.resolve({ metadata: {}, message: { role: 'assistant', content: 'x' } });
declare function mk(o: { complete: () => Promise<Completion> }): void;
mk({ complete: () => Promise.resolve({ metadata: {}, message: { role: 'assistant', content: 'Hello.' } }) });
