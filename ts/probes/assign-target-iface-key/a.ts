// an assignment to an outer let inside a callback: the name's declared type
let stop: () => Promise<void>;
export async function g() {
  await new Promise<number>((resolve) => {
    stop = () =>
      new Promise<void>((r) => {
        r();
      });
    resolve(1);
  });
  await stop();
}
