declare namespace google.maps {
  export class Map { x: number }
}
declare interface Tags extends google.maps.TagMap {}
declare namespace google.maps {
  export interface TagMap { "gmp-map": google.maps.Map }
}
declare namespace google.maps.places {
  export interface PlaceMap { a: 1 }
}
declare interface Tags2 extends google.maps.places.PlaceMap {}
declare namespace google.maps.places {
  export interface Inner { m: Map }
}
