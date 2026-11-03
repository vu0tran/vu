// The `knip` module: vknip is a command (knip, vknip) without knip's JavaScript API. Configurations
// import only types from here (types.d.ts), which leave nothing to load at run time.
export const main = () => {
  throw new Error("vknip has no JavaScript API (knip's main()): run the knip command instead");
};
