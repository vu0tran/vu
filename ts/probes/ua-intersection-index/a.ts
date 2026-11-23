import { X } from './missing';
type LogFields = Record<string, unknown> & { sentry?: { skip?: boolean } };
type Logger = { warn(message: string, fields?: LogFields): void };
declare const logger: Logger;
declare const res: X;
declare const n: any;
logger.warn('a', { received: res.results.length });
logger.warn('b', { received: n });
res.results.forEach((result, index) => {
  logger.warn('c', { errorCode: result.code, responseIndex: index });
});
