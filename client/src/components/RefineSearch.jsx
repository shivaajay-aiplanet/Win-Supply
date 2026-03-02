import { useState } from "react";

function RefineSearch({
  sortBy,
  setSortBy,
  brandFilter,
  setBrandFilter,
  availableBrands,
}) {
  const [sortExpanded, setSortExpanded] = useState(false);
  const [filterExpanded, setFilterExpanded] = useState(false);

  const sortOptions = [
    { value: "relevance", label: "Most Relevant", icon: "sparkles" },
    { value: "name_asc", label: "Name: A to Z", icon: "sort-asc" },
    { value: "name_desc", label: "Name: Z to A", icon: "sort-desc" },
    { value: "brand_asc", label: "Brand: A to Z", icon: "sort-asc" },
    { value: "brand_desc", label: "Brand: Z to A", icon: "sort-desc" },
  ];

  const handleSortChange = (value) => {
    setSortBy(value);
  };

  const handleBrandFilterChange = (e) => {
    setBrandFilter(e.target.value);
  };

  return (
    <aside className="w-64 bg-white rounded-2xl shadow-lg flex-shrink-0 overflow-hidden border border-gray-100">
      {/* Header */}
      <div className="px-5 py-4 bg-blue-600">
        <h3 className="text-base font-bold text-white flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
              />
            </svg>
          </div>
          Refine Results
        </h3>
      </div>

      {/* Sort Section */}
      <div className="border-b border-gray-100">
        <button
          onClick={() => setSortExpanded(!sortExpanded)}
          className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <span className="text-sm font-semibold text-gray-800 flex items-center gap-3">
            <div className="p-1.5 bg-blue-100 rounded-lg">
              <svg
                className="w-4 h-4 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"
                />
              </svg>
            </div>
            Sort By
          </span>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
              sortExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${
            sortExpanded ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
          }`}
        >
          <div className="px-4 pb-4 space-y-1">
            {sortOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSortChange(option.value)}
                className={`w-full px-3 py-2.5 rounded-xl text-sm text-left transition-all duration-200 flex items-center gap-3 ${
                  sortBy === option.value
                    ? "bg-blue-50 text-blue-700 font-medium border-2 border-blue-200"
                    : "text-gray-600 hover:bg-gray-50 border-2 border-transparent"
                }`}
              >
                {sortBy === option.value && (
                  <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
                <span className={sortBy === option.value ? "" : "ml-7"}>{option.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Brand Filter Section */}
      <div>
        <button
          onClick={() => setFilterExpanded(!filterExpanded)}
          className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <span className="text-sm font-semibold text-gray-800 flex items-center gap-3">
            <div className="p-1.5 bg-indigo-100 rounded-lg">
              <svg
                className="w-4 h-4 text-indigo-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                />
              </svg>
            </div>
            Filter by Brand
            {brandFilter && (
              <span className="ml-auto mr-2 px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium">
                1
              </span>
            )}
          </span>
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
              filterExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${
            filterExpanded ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
          }`}
        >
          <div className="px-4 pb-4">
            <div className="relative">
              <select
                id="brand-filter-select"
                value={brandFilter}
                onChange={handleBrandFilterChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-sm bg-gray-50 hover:bg-white hover:border-indigo-300 focus:bg-white focus:outline-none focus:ring-4 focus:ring-indigo-100 focus:border-indigo-500 transition-all duration-200 cursor-pointer appearance-none font-medium text-gray-700"
              >
                <option value="">All Brands</option>
                {availableBrands && availableBrands.length > 0 ? (
                  availableBrands.map((brand) => (
                    <option key={brand} value={brand}>
                      {brand}
                    </option>
                  ))
                ) : (
                  <option value="" disabled>
                    No brands available
                  </option>
                )}
              </select>
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            {brandFilter && (
              <button
                onClick={() => setBrandFilter("")}
                className="mt-3 w-full px-3 py-2 text-sm text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Clear Filter
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="px-5 py-4 bg-gradient-to-r from-gray-50 to-blue-50 border-t border-gray-100">
        <div className="text-xs text-gray-500 font-medium mb-2">Quick Stats</div>
        <div className="flex items-center gap-2">
          <div className="flex-1 px-3 py-2 bg-white rounded-lg border border-gray-200 text-center">
            <div className="text-lg font-bold text-blue-600">
              {availableBrands?.length || 0}
            </div>
            <div className="text-xs text-gray-500">Brands</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default RefineSearch;
