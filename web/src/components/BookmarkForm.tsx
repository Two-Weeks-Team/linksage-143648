"use client";

import { useState } from 'react';
import { createBookmark } from '@/lib/api';
import SummaryEditor from '@/components/SummaryEditor';

export default function BookmarkForm() {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [bookmark, setBookmark] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const result = await createBookmark({ url, title });
      setBookmark(result);
      setUrl('');
      setTitle('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded p-4 shadow-sm bg-white">
      <h2 className="text-xl font-semibold mb-4">Save a New Link</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="url">
            URL
          </label>
          <input
            id="url"
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="https://example.com/article"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="title">
            Title (optional)
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Article title"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Save & Summarize'}
        </button>
      </form>

      {error && <p className="mt-2 text-red-600">{error}</p>}

      {bookmark && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-2">Generated Summary</h3>
          <SummaryEditor bookmarkId={bookmark.id} initialContent={bookmark.summary} />
        </div>
      )}
    </div>
  );
}
