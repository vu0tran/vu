type DefaultPlugins = { cleanupIds: { x?: number }; removeViewBox: void };
type Opt = DefaultPlugins & { 'preset-default': { overrides?: { [K in keyof DefaultPlugins]?: DefaultPlugins[K] | false } }; prefixIds: { prefix?: string } };
type Req = { addAttr: { a: string } };
type PluginConfig =
  | keyof Opt
  | { [Name in keyof Opt]: { name: Name; params?: Opt[Name] } }[keyof Opt]
  | { [Name in keyof Req]: { name: Name; params: Req[Name] } }[keyof Req]
  | { name: string; fn: () => void };
export const c: PluginConfig[] = [{ name: 'preset-default', params: { overrides: { cleanupIds: false, removeViewBox: false } } }];
export const d: PluginConfig[] = ['prefixIds', { name: 'prefixIds', params: { prefix: 'x' } }];
export const e: PluginConfig = { name: 'prefixIds', params: { prefix: 'x' } };
