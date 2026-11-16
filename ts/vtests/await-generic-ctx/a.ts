export class Client {
  private async request<T>(m: string): Promise<T> { return m as T; }
  async get<T>(p: string): Promise<T> { return await this.request(p); }
  async get2<T>(p: string): Promise<T> { return this.request(p); }
  async get3(p: string): Promise<number> { return await this.request(p); }
}
