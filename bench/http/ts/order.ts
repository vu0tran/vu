// The JSON endpoint's work, shared by the TypeScript servers (see ../gen_order.py).
type Item = { sku: string; qty: number; price_cents: number; gift?: boolean };
type Order = { id: string; customer: { name: string }; coupon?: string; items: Item[] };

export function order(body: string): string {
  const o: Order = JSON.parse(body);
  let quantity = 0, subtotal = 0, gifts = 0;
  const bulk: string[] = [];
  for (const it of o.items) {
    quantity += it.qty;
    subtotal += it.qty * it.price_cents;
    if (it.gift) gifts++;
    if (it.qty >= 5) bulk.push(it.sku);
  }
  const discount = o.coupon === "SAVE10" ? Math.floor(subtotal / 10) : 0;
  return JSON.stringify({ id: o.id, customer: o.customer.name, items: o.items.length, quantity, subtotal,
                          discount, total: subtotal - discount, gifts, bulk });
}

export function errorJSON(e: unknown): string {
  return JSON.stringify({ error: e instanceof Error ? e.message : String(e) });
}
