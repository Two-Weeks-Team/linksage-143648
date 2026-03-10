"use client";

import { useEffect, useState } from 'react';
import { fetchTags } from '@/lib/api';

export default function TagCloud() {
  const [tags, setTags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchTags();
        setTags(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <p>Loading tags...</p>;
  if (error) return <p className="text-red-600">{error}</p>;

  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag) => (
        <span
          key={tag.id}
          className="px-3 py-1 bg-gray-200 rounded-full text-sm text-gray-800"
        >
          {tag.name}
        </span>
      ))}
    </div>
  );
}
