type Payloads<LM> = { [E in keyof LM]: unknown };
type Listener<P> = (payload: P) => void;
interface EventBus<LM extends Payloads<LM> = Record<string, any>> {
  on<EN extends keyof LM & string>(eventName: EN, fn: Listener<LM[EN]>): void;
  emit<EN extends keyof LM & string>(eventName: EN, event?: LM[EN]): void;
}
export function make<LM extends Payloads<LM> = Record<string, any>>(): EventBus<LM> {
  return {
    on(eventName, fn) {
      const n: number = eventName;
      this.emit(eventName);
      this.emit(5);
    },
    emit(eventName, event) {
      const s: string = eventName;
      const k: boolean = event;
    },
  };
}
const bus = make<{ a: number; b: string }>();
bus.on("a", (p) => { const q: string = p; });
bus.emit("b", 1);
