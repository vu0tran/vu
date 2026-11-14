declare module "sa" {
  class SAReq { constructor(m: string); method: string; }
  namespace request {
    interface Request extends SAReq { extra?: number }
    interface Static { (u: string): Request; Request: typeof SAReq; }
  }
  const request: request.Static;
  export = request;
}
