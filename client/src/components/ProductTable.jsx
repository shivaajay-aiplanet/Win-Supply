function ProductTable({
  loading,
  searchLoading,
  error,
  isSearchMode,
  searchResults,
  products,
  exactMatchId,
  isHybridSearch,
  pagination,
  handlePreviousPage,
  handleNextPage,
  showScores,
}) {
  return (
    <main className="flex-1 bg-white rounded-xl shadow-lg flex flex-col overflow-hidden border border-gray-200">
      {(loading || searchLoading) && (
        <div className="text-center py-16 text-gray-600">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-sm font-medium">
            {searchLoading ? "Searching products..." : "Loading products..."}
          </p>
        </div>
      )}

      {error && (
        <div className="text-center py-10 text-red-600 bg-red-50 m-4 rounded-lg border border-red-200">
          <p className="font-semibold">Error: {error}</p>
        </div>
      )}

      {!loading && !searchLoading && !error && (
        <>
          <div className="flex-1 overflow-auto px-5">
            <table className="w-full">
              <thead className="bg-gradient-to-r from-gray-100 to-gray-50 border-b-2 border-blue-200 sticky top-0">
                <tr>
                  {isSearchMode && showScores && (
                    <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 w-32 uppercase tracking-wider">
                      {isHybridSearch ? "Relevance Score" : "BM25 Score"}
                    </th>
                  )}
                  <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 w-20 uppercase tracking-wider">
                    Image
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 uppercase tracking-wider">
                    Item Name
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 uppercase tracking-wider">
                    Brand
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 uppercase tracking-wider">
                    Item Number
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 uppercase tracking-wider">
                    Catalog Number
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 uppercase tracking-wider">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody>
                {(isSearchMode ? searchResults?.results || [] : products).map(
                  (item) => {
                    // Handle both hybrid search (direct product) and regular search (item.document)
                    const product = isSearchMode
                      ? isHybridSearch
                        ? item
                        : item.document
                      : item;
                    const productId = isSearchMode
                      ? isHybridSearch
                        ? item.id
                        : item.id
                      : product.id;
                    const isExactMatch =
                      isSearchMode && productId === exactMatchId;

                    return (
                      <tr
                        key={productId}
                        className={`border-b border-gray-100 hover:bg-blue-50 hover:shadow-sm transition-all duration-150 ${
                          isExactMatch
                            ? "bg-gradient-to-r from-green-50 to-green-100 border-l-4 border-l-green-500 shadow-sm"
                            : ""
                        }`}
                      >
                        {isSearchMode && showScores && (
                          <td className="px-4 py-4">
                            <div className="flex flex-col items-start gap-1">
                              {isHybridSearch ? (
                                <>
                                  <div className="flex items-center gap-2">
                                    <span className="bg-purple-600 text-white px-2 py-1 rounded text-xs font-bold">
                                      {item.match_score || 0}%
                                    </span>
                                  </div>
                                  {item.varying_attributes &&
                                    item.varying_attributes.length > 0 && (
                                      <div className="flex flex-wrap gap-1 text-xs">
                                        {item.varying_attributes.map(
                                          (attr, idx) => (
                                            <span
                                              key={idx}
                                              className="bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded"
                                            >
                                              {attr}
                                            </span>
                                          )
                                        )}
                                      </div>
                                    )}
                                </>
                              ) : (
                                <span className="bg-blue-600 text-white px-2 py-1 rounded text-xs font-bold">
                                  {item.score.toFixed(2)}
                                </span>
                              )}
                              {isExactMatch && (
                                <span className="text-green-600 text-xs font-semibold">
                                  ✓ Best Match
                                </span>
                              )}
                            </div>
                          </td>
                        )}
                        <td className="px-4 py-4">
                          <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center">
                            <svg
                              className="w-8 h-8 text-gray-400"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                              xmlns="http://www.w3.org/2000/svg"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                              />
                            </svg>
                          </div>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-800">
                          <div className="font-medium">
                            {product.win_item_name || "N/A"}
                          </div>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-800">
                          {product.brand_name || "N/A"}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-800">
                          {product.wise_item_number || "N/A"}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-800">
                          {product.catalog_number || "N/A"}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          {product.mainframe_description || "N/A"}
                        </td>
                      </tr>
                    );
                  }
                )}
              </tbody>
            </table>
          </div>

          {/* Footer with Pagination */}
          <div className="flex justify-between items-center px-5 py-4 border-t border-gray-200 bg-white flex-shrink-0">
            <div className="text-sm text-gray-600">
              {isSearchMode ? (
                <>
                  {searchResults?.returned_count || 0} results shown |{" "}
                  {searchResults?.total_hits.toLocaleString() || 0} total
                  matches
                </>
              ) : (
                <>0 items selected | {pagination.total_count} results found</>
              )}
            </div>
            {!isSearchMode && (
              <div className="flex items-center gap-4">
                <button
                  onClick={handlePreviousPage}
                  disabled={!pagination.has_previous}
                  className="px-4 py-2 border border-gray-300 bg-white rounded text-sm hover:bg-gray-50 hover:border-blue-600 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ← Previous
                </button>
                <span className="text-sm text-gray-600">
                  Page {pagination.page} of {pagination.total_pages}
                </span>
                <button
                  onClick={handleNextPage}
                  disabled={!pagination.has_next}
                  className="px-4 py-2 border border-gray-300 bg-white rounded text-sm hover:bg-gray-50 hover:border-blue-600 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next →
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </main>
  );
}

export default ProductTable;
