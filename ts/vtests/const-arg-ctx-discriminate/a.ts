// a const type parameter's context-sensitive argument: its constraint's union property type
// discriminated by the literal's members, as outside a const context
// (getApparentTypeOfContextualType's discriminateContextualTypeByObjectMembers)
type Invoke =
  | { src: 'a'; input?: (x: { n: number }) => number; done?: (e: { out: string }) => void }
  | { src: 'b'; input?: (x: { s: string }) => string; done?: (e: { out: boolean }) => void };
interface Config {
  id?: string;
  invoke?: Invoke | readonly Invoke[];
  states?: { [k: string]: Config };
}
declare function make<const T extends Config>(config: T): T;

const m = make({
  id: 'x',
  invoke: { src: 'a', input: ({ n }) => n + 1, done: ({ out }) => { out.toUpperCase(); } },
  states: {
    s: { invoke: [{ src: 'b', input: ({ s }) => s, done: ({ out }) => { const b: number = out; } }] },
  },
});
const id: number = m.id;
