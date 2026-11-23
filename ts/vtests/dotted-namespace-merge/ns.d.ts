declare namespace gg.maps {
  export interface A { a: 1 }
}
interface W extends gg.maps.A {}
declare namespace gg.maps {
  export interface B { b: 2 }
}
interface W2 extends gg.maps.B {}
declare namespace hh { export interface C { c: 3 } }
interface W3 extends hh.C {}
