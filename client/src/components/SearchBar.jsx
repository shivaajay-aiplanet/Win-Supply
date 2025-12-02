function SearchBar({
  searchQuery,
  setSearchQuery,
  searchType,
  setSearchType,
  topK,
  setTopK,
  handleSearch,
  handleReset,
  searchLoading,
  isSearchMode,
  searchResults,
  isHybridSearch,
  exactMatchId,
}) {
  const handleSearchKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div className="bg-gradient-to-r from-white to-blue-50 p-5 rounded-xl shadow-md border border-gray-200">
      <div className="flex gap-3 mb-3">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder={
              searchType === "wise_item_number"
                ? "Enter WISE Item Number..."
                : "Search by Product Name, Description, Brand, Item Number, or Catalog Number..."
            }
            className="w-full px-4 py-3 pl-11 border-2 border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-200 transition-all shadow-sm"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
          />
          <svg
            className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <select
          className="px-4 py-3 border-2 border-gray-300 rounded-lg text-sm min-w-[180px] bg-white hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all cursor-pointer shadow-sm font-medium"
          value={searchType}
          onChange={(e) => setSearchType(e.target.value)}
          title="Search Type"
        >
          <option value="all_fields">All Fields</option>
          <option value="wise_item_number">WISE Item Number</option>
        </select>
        <select
          className="px-4 py-3 border-2 border-gray-300 rounded-lg text-sm min-w-[150px] bg-white hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all cursor-pointer shadow-sm font-medium"
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
        >
          <option value={10}>Top 10 Results</option>
          <option value={20}>Top 20 Results</option>
          <option value={50}>Top 50 Results</option>
          <option value={100}>Top 100 Results</option>
        </select>
        <button
          className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-8 py-3 rounded-lg text-sm font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
          onClick={handleSearch}
          disabled={!searchQuery.trim() || searchLoading}
        >
          {searchLoading ? "Searching..." : "Search"}
        </button>
        <button
          className="bg-white text-gray-700 px-6 py-3 rounded-lg text-sm font-semibold border-2 border-gray-300 hover:bg-gray-100 hover:border-gray-400 transition-all shadow-sm"
          onClick={handleReset}
        >
          Reset
        </button>
      </div>

      {/* Search Results Summary
      {isSearchMode && searchResults && (
        <div className="flex items-center gap-4 text-sm flex-wrap">
          {isHybridSearch && (
            <div className="flex items-center gap-2">
              <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-xs font-semibold">
                🔬 Hybrid Search
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">
              {isHybridSearch ? "WISE Item:" : "Search Query:"}
            </span>
            <span className="text-blue-600 font-medium">
              "{isHybridSearch ? searchResults.wise_item_number : searchResults.query}"
            </span>
          </div>
          {isHybridSearch && searchResults.source_product && (
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-700">Product:</span>
              <span className="text-gray-600 text-xs">
                {searchResults.source_product.win_item_name}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">
              Total Matches:
            </span>
            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded font-semibold">
              {searchResults.total_hits.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">Showing:</span>
            <span className="text-gray-600">
              {searchResults.returned_count} results
            </span>
          </div>
          {exactMatchId && (
            <div className="ml-auto">
              <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-semibold">
                ✓ Best Match Found
              </span>
            </div>
          )}
        </div>
      )} */}
    </div>
  );
}

export default SearchBar;
