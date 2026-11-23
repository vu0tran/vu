declare module "bufx" {
  global {
    interface Bx<T extends ArrayBufferLike = ArrayBufferLike> { t: T }
    interface BxCtor { from(a: W<ArrayLike<number>>): Bx<ArrayBuffer> }
  }
}
