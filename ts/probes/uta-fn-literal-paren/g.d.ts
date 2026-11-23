export {};
declare global {
  function fetch(input: string | URL | Request, init?: RequestInit): Promise<Response>;
}
