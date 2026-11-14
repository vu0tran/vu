type Payloads<LM> = { [E in keyof LM]: unknown };
type Listener<P> = (payload: P) => void;
interface EventBus<LM extends Payloads<LM> = Record<string, any>> {
  on<EN extends keyof LM & string>(eventName: EN, fn: Listener<LM[EN]>): void;
  off<EN extends keyof LM & string>(eventName: EN, fn: Listener<LM[EN]>): void;
  once<EN extends keyof LM & string>(eventName: EN, fn: Listener<LM[EN]>): void;
}
export function createEventBus<LM extends Payloads<LM> = Record<string, any>>(): EventBus<LM> {
  return {
    on(eventName, fn) {},
    off(eventName, fn) {},
    once(eventName, fn) {
      const handler: typeof fn = (payload) => { this.off(eventName, handler); fn(payload); };
      this.on(eventName, handler);
    },
  };
}
