declare const h: { options: { clock(): Date; name: string; enroll(q: number): string } };
declare function eq(a: unknown, b: unknown): void;
const ports = {
  ...h.options,
  timeMs: 5,
  enrollment: h.options.enroll,
  clock() {
    return new Date(this.timeMs);
  },
  other(q: number) {
    return this.enrollment(q);
  },
};
const n1: number = ports.clock();
const n2: number = ports.other(1);
const options = {
  ...h.options,
  database: {
    query() {
      eq(this, options.database);
      return 1;
    },
  },
  clock() {
    eq(this, options);
    const s: string = this.name;
    return new Date();
  },
};
const n3: string = options.database.query();
const events: unknown[] = [];
const sink = {
  events,
  report(event: unknown) {
    this.events.push(event);
    const u: string = this.events;
    return 1;
  },
};
const n4: string = sink.report(1);
declare const base: { a: number; b: string; m(): number; opt?: boolean };
const o1 = {
  ...base,
  a: 'x',
  f() {
    const s: number = this.a;
    return this.b;
  },
};
const r1: number = o1.f();
const o2 = {
  a: 1,
  ...base,
  g() {
    const s: string = this.a;
    return this.opt;
  },
};
const r2: string = o2.g();
const o3 = {
  ...base,
  ...{ c: 1 },
  h() {
    return this.c + this.m();
  },
};
const r3: string = o3.h();
