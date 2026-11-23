// SymbolConstructor augmented with a plain symbol (xstate: observable: symbol): [Symbol.observable]
// is not a late-bindable name, so the interface member is no property and A is assignable to I
// (xstate's Actor to AnyActorRef, for waitFor's snapshot type).
import { A, I } from "fake";
declare const a: A;
const i: I = a;
const z: string = i;
