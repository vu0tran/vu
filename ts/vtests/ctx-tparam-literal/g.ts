export {};
declare function g<M extends { o?: "a" }>(m: M): M;
declare function h<M extends { o: "a" | undefined }>(m: M): M;
declare function k<M extends { o: "a" | 1 }>(m: M): M;
declare function l<M extends { o: true | 1 }>(m: M): M;
const x3: number = g({ o: "a" });
const x4: number = h({ o: "a" });
const x5: number = k({ o: "a" });
const x6: number = l({ o: true });
