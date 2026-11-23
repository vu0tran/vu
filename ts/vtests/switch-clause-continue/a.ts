// A switch clause left by continue (its end not reached): no path of its own into the join.
enum WS { A = 'A', B = 'B', C = 'C' }
enum PS { Done = 'done', Cancel = 'cancel' }
declare function hasRealDate(d: string | null | undefined): d is string;
type Order = { state: WS; validatedAt: string | null };
export function h(orders: Order[]) {
  const result: { status: PS; occurredAt: string | null }[] = [];
  for (const order of orders) {
    let status: PS;
    let timestamp: string | null = null;
    switch (order.state) {
      case WS.A:
        status = PS.Done;
        timestamp = order.validatedAt;
        break;
      case WS.B:
        status = PS.Cancel;
        break;
      default:
        continue;
    }
    result.push({ status, occurredAt: hasRealDate(timestamp) ? timestamp : null });
    const n: number = timestamp;
    const m: string = status;
  }
  return result;
}
export function g(xs: number[]) {
  for (const x of xs) {
    let y: string | number | boolean = true;
    switch (x) {
      case 1:
        y = 'a';
        break;
      case 2:
        if (x) continue;
        y = 2;
        break;
      default:
        if (x > 3) { y = false; continue; } else continue;
    }
    const z: boolean = y;
  }
}
