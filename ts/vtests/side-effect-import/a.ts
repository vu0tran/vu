// import "x": TS2882 when it resolves to nothing (noUncheckedSideEffectImports, on by default).
import "./nope";
import "nopkg";
export {};
