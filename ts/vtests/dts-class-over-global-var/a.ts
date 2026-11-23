export const s = new ReadableStream<Uint8Array>({
  start(stream) {
    stream.enqueue(new Uint8Array(1));
    const n: number = stream.enqueue;
  },
});
