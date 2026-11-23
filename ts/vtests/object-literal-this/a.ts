export const OH = {
  note: 'x',
  startTime: {
    hour: '9',
    minute: '00',
    get combined() { return `${this.hour}:${this.minute}`; },
    n: 1,
    plus() { return this.n + 1; },
  },
};
export const z: number = OH.startTime.combined;
export const y: string = OH.startTime.plus();
