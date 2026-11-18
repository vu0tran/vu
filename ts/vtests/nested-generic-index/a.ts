export const templates = {
  declarative: { githubIssues: 1, custom: 'x' },
  programmatic: { example: true, other: 2 },
} as const;
export type TemplateMap = typeof templates;
export type TemplateType = keyof TemplateMap;
export type TemplateName<T extends TemplateType> = keyof TemplateMap[T];
export function getTemplate<T extends TemplateType, N extends TemplateName<T>>(type: T, name: N): TemplateMap[T][N] {
  return templates[type][name];
}
export function g2<T extends TemplateType, N extends TemplateName<T>>(type: T, name: N): number {
  return templates[type][name];
}
export function h<T extends TemplateType>(type: T): number {
  const y = templates[type];
  return y;
}
