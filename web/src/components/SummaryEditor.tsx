"use client";

import { useState } from 'react';
import { getRelatedLinks } from '@/lib/api';

interface Props {
  bookmarkId: string;
  initialContent: string;
}

export default function SummaryEditor({ bookmarkId, initialContent }: Props) {
  const [content, setContent] = useState(initialContent);
  const [related, setRelated] = useState<any[]>([]);
  const [loadingRelated, setLoadingRelated] = useState(false);
  const [error, setError] = useState('');

  const fetchRelated = async () => {
    setLoadingRelated(true);
    setError('');
    try {
      const data = await getRelatedLinks(bookmarkId);
      setRelated(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoadingRelated(false);
    }
  };

  return (
    <div className="space-y-4">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={6}
        className="w-full border rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        onClick={fetchRelated}
        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
      >
        {loadingRelated ? 'Loading...' : 'Show Related Links'}
      </button>
      {error && <p className="text-red-600">{error}</p>}
      {related.length > 0 && (
        <ul className="list-disc pl-5 mt-2">
          {related.map((link) => (
            <li key={link.id} className="text-blue-600 underline">
              {link.title || link.url}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
