declare module "fs2" {
  export function existsSync(p: string): boolean;
  export const sep: string;
}
declare module "node:fs2" {
  export * from "fs2";
}
declare module "node:other" {
  export * from "nowhere";
  export function here(): void;
}
