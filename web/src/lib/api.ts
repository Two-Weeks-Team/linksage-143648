export const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

/**
 * Create a new bookmark. The backend will start an AI summarization job and return the bookmark
 * (including the generated summary when ready).
 */
export async function createBookmark(data: {
  url: string;
  title?: string;
}): Promise<any> {
  const response = await fetch(`${API_BASE}/bookmarks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err?.error?.message || 'Failed to create bookmark');
  }
  return response.json();
}

/**
 * Retrieve related links for a given bookmark ID.
 */
export async function getRelatedLinks(bookmarkId: string): Promise<any[]> {
  const response = await fetch(`${API_BASE}/bookmarks/${bookmarkId}/related`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err?.error?.message || 'Failed to fetch related links');
  }
  return response.json();
}

/**
 * Search the knowledge library.
 */
export async function searchLinks(query: string, page = 1): Promise<any> {
  const params = new URLSearchParams({ query, page: page.toString() });
  const response = await fetch(`${API_BASE}/search?${params.toString()}`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err?.error?.message || 'Search failed');
  }
  return response.json();
}

/**
 * Get the list of all tags (both AI‑generated and user defined).
 */
export async function fetchTags(): Promise<any[]> {
  const response = await fetch(`${API_BASE}/tags`);
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err?.error?.message || 'Failed to fetch tags');
  }
  return response.json();
}
