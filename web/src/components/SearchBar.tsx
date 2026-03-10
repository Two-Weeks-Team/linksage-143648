"use client";

import { useState } from 'react';
import { searchLinks } from '@/lib/api';

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await searchLinks(query);
      setResults(data.results ?? []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded p-4 bg-white shadow-sm">
      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search your library..."
          className="flex-1 border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>
      {error && <p className="text-red-600 mb-2">{error}</p>}
      {results.length > 0 && (
        <ul className="space-y-2">
          {results.map((item) => (
            <li key={item.id} className="p-3 border rounded bg-gray-50">
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="font-medium text-blue-600 underline">
                {item.title}
              </a>
              <p className="text-sm text-gray-600">Score: {(item.score * 100).toFixed(1)}%</p>
              {item.why_relevant && <p className="text-xs text-gray-500">{item.why_relevant}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
