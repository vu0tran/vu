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
function fixture() {
  const context = { id: 1 };
  return {
    context,
    read() {
      return this.context.id;
    },
  };
}
const n5: string = fixture().read();
