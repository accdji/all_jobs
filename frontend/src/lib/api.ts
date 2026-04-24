function buildApiUrl(path: string) {
  const normalizedPath = path.replace(/^\/+/, "");

  if (typeof window !== "undefined") {
    return `/api/${normalizedPath}`;
  }

  const baseUrl = process.env.INTERNAL_API_ORIGIN ?? "http://127.0.0.1:8000/api";
  return `${baseUrl.replace(/\/+$/, "")}/${normalizedPath}`;
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}

export async function putJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}

export async function postForm<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "POST",
    body,
  });

  if (!response.ok) {
    throw new Error(`Request failed for ${path}`);
  }

  return response.json() as Promise<T>;
}
