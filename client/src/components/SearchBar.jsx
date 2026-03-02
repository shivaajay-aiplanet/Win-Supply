import { useState } from "react";

function SearchBar({
  searchQuery,
  setSearchQuery,
  searchType,
  setSearchType,
  handleSearch,
  handleReset,
  searchLoading,
}) {
  const [isFocused, setIsFocused] = useState(false);

  const handleSearchKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div
      className={`bg-white p-5 rounded-2xl border transition-all duration-300 ${
        isFocused
          ? "shadow-[0_0_30px_rgba(59,130,246,0.3)] border-blue-300"
          : "shadow-lg border-gray-200 hover:shadow-xl"
      }`}
    >
      <div className="flex gap-3 flex-wrap items-center">
        <div className="flex-1 relative group">
          <div
            className={`absolute inset-0 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl opacity-0 blur transition-opacity duration-300 ${
              isFocused ? "opacity-20" : "group-hover:opacity-10"
            }`}
          ></div>
          <input
            type="text"
            placeholder={
              searchType === "wise_item_number"
                ? "Enter WISE Item Number..."
                : "Search by Product Name, Description, Brand, Item Number, or Catalog Number..."
            }
            className="relative w-full px-4 py-3.5 pl-12 border-2 border-gray-200 rounded-xl text-sm bg-gray-50 focus:bg-white focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-200 placeholder-gray-400"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
          />
          <div
            className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-all duration-200 ${
              isFocused ? "text-blue-500 scale-110" : "text-gray-400"
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>
        <select
          className="px-4 py-3.5 border-2 border-gray-200 rounded-xl text-sm min-w-[180px] bg-gray-50 hover:bg-white hover:border-blue-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 cursor-pointer font-medium text-gray-700"
          value={searchType}
          onChange={(e) => setSearchType(e.target.value)}
          title="Search Type"
        >
          <option value="wise_item_number">WISE Item Number</option>
          <option value="all_fields">All Fields</option>
        </select>
        <button
          className="bg-blue-600 text-white px-8 py-3.5 rounded-xl text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl active:scale-[0.98] flex items-center gap-2"
          onClick={handleSearch}
          disabled={searchLoading}
        >
          {searchLoading ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Searching...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Search
            </>
          )}
        </button>
        <button
          className="px-6 py-3.5 rounded-xl text-sm font-semibold border-2 border-gray-200 text-gray-600 bg-white hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800 transition-all duration-200 hover:shadow-md active:scale-[0.98]"
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
