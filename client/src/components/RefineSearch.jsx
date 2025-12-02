function RefineSearch({
  sortBy,
  setSortBy,
  brandFilter,
  setBrandFilter,
  availableBrands,
}) {
  const sortOptions = [
    { value: "relevance", label: "Most Relevant" },
    { value: "name_asc", label: "Name: A to Z" },
    { value: "name_desc", label: "Name: Z to A" },
    { value: "brand_asc", label: "Brand: A to Z" },
    { value: "brand_desc", label: "Brand: Z to A" },
  ];

  const handleSortChange = (e) => {
    setSortBy(e.target.value);
  };

  const handleBrandFilterChange = (e) => {
    setBrandFilter(e.target.value);
  };

  return (
    <aside className="w-64 bg-white rounded-xl shadow-lg flex-shrink-0 overflow-y-auto border border-gray-200">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
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
          Refine Results
        </h3>
      </div>

      {/* Sort Section */}
      <div className="px-5 py-4 border-b border-gray-100 bg-gray-50">
        <label
          htmlFor="sort-select"
          className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2"
        >
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
          Sort By
        </label>
        <select
          id="sort-select"
          value={sortBy}
          onChange={handleSortChange}
          className="w-full px-3 py-2.5 border-2 border-gray-300 rounded-lg text-sm bg-white hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all cursor-pointer shadow-sm"
        >
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Brand Filter Section */}
      <div className="px-5 py-4 bg-gray-50">
        <label
          htmlFor="brand-filter-select"
          className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-2"
        >
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
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
            />
          </svg>
          Filter by Brand
        </label>
        <select
          id="brand-filter-select"
          value={brandFilter}
          onChange={handleBrandFilterChange}
          className="w-full px-3 py-2.5 border-2 border-gray-300 rounded-lg text-sm bg-white hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all cursor-pointer shadow-sm"
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
      </div>
    </aside>
  );
}

export default RefineSearch;
