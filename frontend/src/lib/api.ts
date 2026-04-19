export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}
