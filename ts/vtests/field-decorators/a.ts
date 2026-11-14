declare function Memoized<T = unknown>(target: object, propertyKey: string | symbol, descriptor?: TypedPropertyDescriptor<T>): TypedPropertyDescriptor<T>;
declare const OnEv: (e: string) => MethodDecorator;
declare const OnSh: (p?: number) => MethodDecorator;
class A {
  @Memoized
  normalProperty = 42;
  @OnEv('x')
  notAFunction = 'string';
  @OnEv('x')
  async m() {}
  @Memoized
  get g() { return 1; }
}
class TestService {
  @OnSh(10)
  async onShutdown() {}
}
