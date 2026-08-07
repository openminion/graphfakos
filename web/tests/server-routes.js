const host = "127.0.0.1";

export const testServers = {
  dense: {
    port: 8793,
    baseURL: `http://${host}:8793`,
  },
  scale200k: {
    port: 8794,
    baseURL: `http://${host}:8794`,
  },
  scale1m: {
    port: 8795,
    baseURL: `http://${host}:8795`,
  },
};

export function testServerUrl(server, path = "/explore", query = "") {
  const suffix = query ? `?${query.replace(/^\?/, "")}` : "";
  return `${testServers[server].baseURL}${path}${suffix}`;
}
