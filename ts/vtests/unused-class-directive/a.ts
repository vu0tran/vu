declare function Service(): ClassDecorator;
declare const OnEv: (e: string) => MethodDecorator;
export function f() {
  @Service()
  // @ts-expect-error unused class
  class TestService {
    @OnEv('x')
    async m() {}
  }
  class Used {}
  // @ts-expect-error not unused
  const u: number = 1;
  return [new Used(), u];
}
export function g() {
  // @ts-expect-error unused class
  class Other {}
  return 1;
}
