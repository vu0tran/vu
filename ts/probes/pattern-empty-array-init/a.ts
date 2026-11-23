declare const g: any;
declare function load(): Promise<{ customers: { uuid: string }[] }>;
export async function f(n: number) {
  const { customers } = n ? await load() : { customers: [] };
  const names = customers.map((c) => c.uuid.toLowerCase());
  const { items, total } = n ? g : { items: [], total: 0 };
  const { list } = n ? await g.fetch() : { list: [] };
  return [names, items, total, list.length];
}
