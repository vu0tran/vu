// methods in an object literal under as const: their function types, the properties readonly
export {};
const Service = {
  async list(n: number) { return [n, n * 2]; },
  name: 'svc',
  get(k: string) { return { k, at: 1 }; },
} as const;
const a: number = Service.list;
const b: number = Service.name;
const c: number = Service.get('x');
Service.name = 'other';
const d: string = Service.get('x').at;
