"use client";

import { useState } from 'react';
import BookmarkForm from '@/components/BookmarkForm';
import SearchBar from '@/components/SearchBar';
import TagCloud from '@/components/TagCloud';

export default function HomePage() {
  const [showSearch, setShowSearch] = useState(false);

  return (
    <main className="max-w-4xl mx-auto p-6 space-y-8">
      <section className="text-center">
        <h1 className="text-4xl font-bold mb-2">LinkSage</h1>
        <p className="text-lg text-gray-600">
          Turn Links into Knowledge: Smart Organization, Instant Recall, and Connected Insights with AI
        </p>
      </section>

      <section>
        <BookmarkForm />
      </section>

      <section className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold">Explore Tags</h2>
        <button
          onClick={() => setShowSearch(!showSearch)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showSearch ? 'Hide Search' : 'Search'}
        </button>
      </section>

      {showSearch && (
        <section>
          <SearchBar />
        </section>
      )}

      <section>
        <TagCloud />
      </section>
    </main>
  );
}
