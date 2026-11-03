// The types `import type { ... } from "knip"` names, for configurations (knip.ts, knip.config.ts).
// They follow knip 6.44.1's configuration schema (schema.json) by hand, more loosely than knip's own
// (which zod infers): a plugin's section and any key knip adds later are accepted as `unknown`.
// vknip has no JavaScript API: knip's `main()` and its reporter and preprocessor functions don't run.

export type IssueType =
  | "files" | "dependencies" | "devDependencies" | "optionalPeerDependencies" | "unlisted" | "binaries"
  | "unresolved" | "exports" | "types" | "nsExports" | "nsTypes" | "duplicates" | "enumMembers"
  | "namespaceMembers" | "catalog" | "catalogReferences" | "cycles";

type Patterns = string | string[];
type Ignorable = Array<string | RegExp>;
type ExportsUsedInFile = boolean | Partial<Record<"class" | "enum" | "function" | "interface" | "member" | "type", boolean>>;

/** A plugin's section: on/off, its config files, or its config, entry and project files */
export type PluginConfig = boolean | Patterns | { config?: Patterns; entry?: Patterns; project?: Patterns };

export interface WorkspaceProjectConfig {
  entry?: Patterns;
  project?: Patterns;
  paths?: Record<string, string[]>;
  ignore?: Patterns;
  ignoreFiles?: Patterns;
  ignoreBinaries?: Ignorable;
  ignoreGlobalBinaries?: Ignorable;
  ignoreDependencies?: Ignorable;
  ignoreMembers?: Ignorable;
  ignoreUnresolved?: Ignorable;
  ignoreExportsUsedInFile?: ExportsUsedInFile;
  ignoreIssues?: Record<string, IssueType[]>;
  includeEntryExports?: boolean;
  /** plugin sections (vitest, eslint, next, ...) */
  [plugin: string]: unknown;
}

export interface KnipConfiguration extends WorkspaceProjectConfig {
  $schema?: string;
  ignoreWorkspaces?: string[];
  include?: IssueType[];
  exclude?: IssueType[];
  cycles?: unknown;
  tags?: string[];
  workspaces?: Record<string, WorkspaceProjectConfig>;
  rules?: Partial<Record<IssueType, "error" | "warn" | "off">>;
  preprocessor?: string | string[];
  preprocessorOptions?: string;
  treatConfigHintsAsErrors?: boolean;
  treatTagHintsAsErrors?: boolean;
  compilers?: Record<string, unknown>;
}

/** What a configuration file exports: the configuration, or a function returning it */
export type KnipConfig = KnipConfiguration | ((options: Record<string, unknown>) => KnipConfiguration | Promise<KnipConfiguration>);
