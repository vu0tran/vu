declare const anyVal: any;
export function setup(options: { taskId?: string; enabled?: boolean; extra?: any } = {}) {
  const { taskId, enabled, extra } = {
    taskId: 'task-1' as string | undefined,
    enabled: true,
    ...options,
  };
  const x: string = anyVal;
  return [taskId, enabled, extra, x];
}
