// import "x" with noUncheckedSideEffectImports false: not reported.
import "./nope";
import "nopkg";
import { a } from "./nope2";
export { a };
