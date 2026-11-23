type SprigParams =
  | {
      action: 'track';
      payload: [event: string];
    }
  | {
      action: 'setAttribute';
      payload: [attribute: string, value: string];
    };

type Sprig = <Action extends SprigParams['action']>(
  ...args: Extract<SprigParams, { action: Action }> extends { payload: infer TPayload }
    ? [action: Action, ...payload]
    : [action: Action]
) => void;

interface Window {
  Sprig: Sprig | undefined;
}
