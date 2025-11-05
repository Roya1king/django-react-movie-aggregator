import React, { useState, useEffect, useRef } from 'react';

// You would typically install this with: npm install lucide-react
// For this single-file setup, I'll use simple SVG icons.
const SearchIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-5 w-5"
  >
    <circle cx="11" cy="11" r="8"></circle>
    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
  </svg>
);

const ExternalLinkIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-4 w-4 ml-1 opacity-60 group-hover:opacity-100 transition-opacity"
  >
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
    <polyline points="15 3 21 3 21 9"></polyline>
    <line x1="10" y1="14" x2="21" y2="3"></line>
  </svg>
);

// --- Movie Card Skeleton Component (NEW) ---
/**
 * A placeholder component with a pulse animation to show while results are loading.
 */
function MovieCardSkeleton() {
  return (
    <div className="block bg-white/5 backdrop-blur-sm rounded-lg overflow-hidden shadow-lg">
      <div className="relative animate-pulse">
        {/* Source Badge Placeholder */}
        <div className="absolute top-2 left-2 z-10 bg-gray-600 h-5 w-16 rounded"></div>

        {/* Poster Image Placeholder */}
        <div className="w-full aspect-[2/3] bg-gray-700"></div>
      </div>

      {/* Card Content Placeholder */}
      <div className="p-4 animate-pulse">
        <div className="h-4 bg-gray-600 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-600 rounded w-1/2"></div>
      </div>
    </div>
  );
}

// --- Movie Card Component ---

/**
 * A component to display a single movie result.
 * @param {object} props
 * @param {object} props.movie - The movie result object
 * @param {string} props.movie.title - The title of the movie
 * @param {string} props.movie.link - The direct URL to the movie
 * @param {string} props.movie.poster - The URL for the movie's poster image
 * @param {string} props.movie.source - The name of the source website
 */
function MovieCard({ movie }) {
  const { title, link, poster, source } = movie;

  // Fallback image in case the poster URL is broken
  const handleImageError = (e) => {
    const bgColor = '343a40'; // A dark gray
    const textColor = 'ffffff';
    const placeholderText = title.split(' ').slice(0, 2).join('+');
    e.target.src = `https://placehold.co/500x750/${bgColor}/${textColor}?text=${placeholderText}&font=roboto`;
  };

  return (
    <a
      href={link}
      target="_blank"
      rel="noopener noreferrer"
      className="group block bg-white/5 backdrop-blur-sm rounded-lg overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 ease-in-out transform hover:-translate-y-1"
    >
      <div className="relative">
        {/* Source Badge */}
        <span className="absolute top-2 left-2 z-10 bg-indigo-600 text-white px-2 py-1 text-xs font-bold rounded">
          {source}
        </span>

        {/* Poster Image */}
        <img
          src={poster}
          alt={`Poster for ${title}`}
          onError={handleImageError}
          className="w-full h-auto aspect-[2/3] object-cover transition-transform duration-300 group-hover:scale-105"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
      </div>

      {/* Card Content */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-100 text-base truncate group-hover:text-indigo-300 transition-colors">
          {title}
        </h3>
        <div className="flex items-center text-sm text-gray-400 mt-1 group-hover:text-white">
          Visit Source
          <ExternalLinkIcon />
        </div>
      </div>
    </a>
  );
}

// --- Main App Component ---
function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [sources, setSources] = useState(new Set());
  const [selectedSource, setSelectedSource] = useState('all');
  const [isSearching, setIsSearching] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [error, setError] = useState(null);

  const ws = useRef(null);
  const searchTimeout = useRef(null); // Ref to store timeout

  const WEBSOCKET_URL = 'ws://localhost:8000/ws/search/';

  // Effect to manage WebSocket connection
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
      // Clear timeout on unmount
      if (searchTimeout.current) {
        clearTimeout(searchTimeout.current);
      }
    };
  }, []);

  const connect = () => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionStatus('Connecting...');
    ws.current = new WebSocket(WEBSOCKET_URL);

    ws.current.onopen = () => {
      setConnectionStatus('Connected');
      console.log('WebSocket Connected');
      setError(null);
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.error) {
        console.error('WebSocket Error:', data.message);
        // You could set a specific error message for this source
      } else if (data.source) {
        // Handle a successful result
        setResults((prevResults) => [...prevResults, data]);
        setSources((prevSources) => new Set(prevSources).add(data.source));
      }
    };

    ws.current.onerror = (err) => {
      console.error('WebSocket Error:', err);
      setError('Failed to connect to the server. Is it running?');
      setConnectionStatus('Error');
    };

    ws.current.onclose = () => {
      setConnectionStatus('Disconnected');
      console.log('WebSocket Disconnected');
      // Optional: automatic reconnect
      // setTimeout(connect, 5000);
    };
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchTerm.trim() || isSearching) return; // Don't search if already searching

    // Ensure connection is open before sending
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      setError('Not connected. Trying to reconnect...');
      connect(); // Try to reconnect
      // Wait a bit before trying to send
      setTimeout(() => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          sendSearch();
        } else {
          setError('Could not establish connection to send search.');
        }
      }, 1000);
    } else {
      sendSearch();
    }
  };

  const sendSearch = () => {
    // Clear previous search
    setResults([]);
    setSources(new Set());
    setSelectedSource('all');
    setIsSearching(true);
    setError(null);

    // Send search message
    ws.current.send(
      JSON.stringify({
        action: 'search',
        term: searchTerm,
      })
    );

    // Set a timeout to re-enable the search button after 10 seconds
    searchTimeout.current = setTimeout(() => {
      setIsSearching(false);
    }, 10000); // 10-second cooldown
  };

  // --- Filtering ---
  const filteredResults =
    selectedSource === 'all'
      ? results
      : results.filter((r) => r.source === selectedSource);

  const sourceList = Array.from(sources);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200 font-sans p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* --- Header --- */}
        <header className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">
            Personal Movie Aggregator
          </h1>
          <p className="text-lg text-gray-400">
            Search multiple sites in real-time.
          </p>
          <div className="text-sm mt-2">
            Status:
            <span
              className={`ml-2 font-semibold ${
                connectionStatus === 'Connected'
                  ? 'text-green-400'
                  : 'text-red-400'
              }`}
            >
              {connectionStatus}
            </span>
          </div>
        </header>

        {/* --- Search Bar --- */}
        <form
          onSubmit={handleSearch}
          className="flex max-w-2xl mx-auto mb-8 bg-white/10 rounded-full shadow-lg p-1 backdrop-blur-sm"
        >
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search for 'Dune', 'Oppenheimer'..."
            className="flex-grow bg-transparent text-white placeholder-gray-400 text-lg px-6 py-3 border-none outline-none rounded-full"
          />
          <button
            type="submit"
            className="bg-indigo-600 text-white rounded-full px-6 py-3 hover:bg-indigo-500 transition-colors duration-300 flex items-center disabled:bg-gray-500 disabled:cursor-not-allowed"
            disabled={connectionStatus !== 'Connected' || isSearching}
          >
            <SearchIcon />
            <span className="ml-2 hidden md:inline">
              {isSearching ? 'Searching...' : 'Search'}
            </span>
          </button>
        </form>

        {/* --- Error Display --- */}
        {error && (
          <div className="max-w-2xl mx-auto text-center bg-red-800/50 border border-red-700 text-red-200 px-4 py-3 rounded-lg mb-8">
            {error}
          </div>
        )}

        {/* --- Controls: Filter & Count --- */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-white">
            Results
            <span className="text-base text-gray-400 ml-2">
              ({filteredResults.length} shown)
            </span>
          </h2>

          {sourceList.length > 0 && (
            <div className="flex items-center mt-4 md:mt-0">
              <label htmlFor="source-filter" className="text-gray-400 mr-2">
                Filter by source:
              </label>
              <select
                id="source-filter"
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                className="bg-gray-800 border border-gray-700 text-white text-sm rounded-lg p-2.5 outline-none"
              >
                <option value="all">All Sources</option>
                {sourceList.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* --- Results Grid --- */}
        {results.length > 0 && (
          // We have results, now check filters
          <>
            {filteredResults.length === 0 && (
              // Filtered out all results
              <div className="text-center text-gray-400 py-10">
                <div className="text-xl">No results</div>
                <p>
                  No results match the filter '{selectedSource}'. Try selecting
                  'All Sources'.
                </p>
              </div>
            )}

            {filteredResults.length > 0 && (
              // Show the filtered results
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
                {filteredResults.map((movie, index) => (
                  <MovieCard
                    key={`${movie.link}-${movie.title}-${index}`}
                    movie={movie}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {results.length === 0 && isSearching && (
          // No results YET, and we are searching -> Show Skeleton
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
            {[...Array(10)].map((_, i) => (
              <MovieCardSkeleton key={i} />
            ))}
          </div>
        )}

        {results.length === 0 && !isSearching && (
          // No results, and not searching -> Show "Ready"
          <div className="text-center text-gray-400 py-10">
            <div className="text-xl">Ready to search</div>
            <p>Enter a movie title above to begin.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;