import { useState, useRef, useEffect } from "react";
import ProductDetailModal from "./ProductDetailModal";
import NotFound from "./NotFound";

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
  sourceWiseItemNumber,
  onDeleteMatch,
  onFeedback,
  alternativesMap,
  onAlternativeClick,
  notFound,
  notFoundItemNumber,
}) {
  const [hoveredRowId, setHoveredRowId] = useState(null);
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState({});
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpenId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMenuClick = (productId, e) => {
    e.stopPropagation();
    setMenuOpenId(menuOpenId === productId ? null : productId);
  };

  const handleReportClick = (productId, e) => {
    e.stopPropagation();
    setMenuOpenId(null);
    setConfirmDeleteId(productId);
  };

  const handleConfirmDelete = async (wiseItemNumber) => {
    if (!sourceWiseItemNumber || !wiseItemNumber || !onDeleteMatch) return;

    setDeleteLoading(true);
    try {
      await onDeleteMatch(sourceWiseItemNumber, wiseItemNumber);
      setConfirmDeleteId(null);
    } catch (error) {
      console.error("Error deleting match:", error);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleCancelDelete = () => {
    setConfirmDeleteId(null);
  };

  const handleFeedback = async (wiseItemNumber, feedbackType) => {
    if (!sourceWiseItemNumber || !wiseItemNumber || !onFeedback) return;

    const key = `${wiseItemNumber}-${feedbackType}`;
    setFeedbackLoading((prev) => ({ ...prev, [key]: true }));
    try {
      await onFeedback(sourceWiseItemNumber, wiseItemNumber, feedbackType);
    } catch (error) {
      console.error("Error submitting feedback:", error);
    } finally {
      setFeedbackLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  // Handle row click to open modal
  const handleRowClick = (product) => {
    setSelectedProduct(product);
    setIsModalOpen(true);
  };

  // Handle modal close
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedProduct(null);
  };

  return (
    <main className="flex-1 bg-white rounded-xl shadow-lg flex flex-col overflow-hidden border border-gray-200">
      {/* Product Detail Modal */}
      <ProductDetailModal
        product={selectedProduct}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />

      {(loading || searchLoading) && (
        <div className="text-center py-16 text-gray-600">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-sm font-medium">
            {searchLoading ? "Searching products..." : "Loading products..."}
          </p>
        </div>
      )}

      {error && !notFound && (
        <div className="text-center py-10 text-red-600 bg-red-50 m-4 rounded-lg border border-red-200">
          <p className="font-semibold">Error: {error}</p>
        </div>
      )}

      {notFound && !loading && !searchLoading && (
        <NotFound itemNumber={notFoundItemNumber} />
      )}

      {/* Confirmation Modal */}
      {confirmDeleteId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Remove Similar Product?
            </h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to remove this product from similar matches?
              This will update the cross-reference data and the product will no
              longer appear in similar results for this search.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={handleCancelDelete}
                disabled={deleteLoading}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const item = (searchResults?.results || []).find(
                    (r) => (isHybridSearch ? r.id : r.id) === confirmDeleteId
                  );
                  const wiseItemNumber = isHybridSearch
                    ? item?.wise_item_number
                    : item?.document?.wise_item_number;
                  handleConfirmDelete(wiseItemNumber);
                }}
                disabled={deleteLoading}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
              >
                {deleteLoading && (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                )}
                Remove
              </button>
            </div>
          </div>
        </div>
      )}

      {!loading && !searchLoading && !error && !notFound && (
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
                  {/* Alternative Product column - only show in regular browse mode */}
                  {!isSearchMode && (
                    <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 uppercase tracking-wider">
                      Alternative Product
                    </th>
                  )}
                  {/* Actions column header - only show in hybrid search mode */}
                  {isSearchMode && isHybridSearch && (
                    <th className="px-4 py-4 text-left text-xs font-bold text-gray-800 w-12 uppercase tracking-wider"></th>
                  )}
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
                    // Show menu only for similar products (not exact match) in hybrid search mode
                    const showActionMenu =
                      isSearchMode && isHybridSearch && !isExactMatch;

                    return (
                      <tr
                        key={productId}
                        className={`group border-b border-gray-100 hover:bg-blue-50 hover:shadow-sm transition-all duration-150 ${
                          isExactMatch
                            ? "bg-gradient-to-r from-green-50 to-green-100 border-l-4 border-l-green-500 shadow-sm"
                            : ""
                        }`}
                        onMouseEnter={() => setHoveredRowId(productId)}
                        onMouseLeave={() => {
                          setHoveredRowId(null);
                          // Don't close menu if mouse leaves row but menu is open
                        }}
                      >
                        {isSearchMode && showScores && (
                          <td className="px-4 py-4">
                            <div className="flex flex-col items-start gap-2">
                              {isHybridSearch ? (
                                <>
                                  <span
                                    className={`px-3 py-1 rounded text-xs font-bold text-white ${
                                      (item.match_score || 0) === 100
                                        ? "bg-green-600"
                                        : (item.match_score || 0) >= 90
                                        ? "bg-green-500"
                                        : (item.match_score || 0) >= 80
                                        ? "bg-yellow-500"
                                        : "bg-orange-500"
                                    }`}
                                  >
                                    {item.match_score || 0}%
                                  </span>
                                  {item.varying_attributes &&
                                    item.varying_attributes.length > 0 && (
                                      <div className="flex flex-wrap items-center gap-1.5 text-xs">
                                        <span className="text-gray-500 font-medium">
                                          Differs in:
                                        </span>
                                        {item.varying_attributes.map(
                                          (attr, idx) => (
                                            <span
                                              key={idx}
                                              className="border border-yellow-400 text-yellow-700 px-2 py-0.5 rounded-full text-xs capitalize"
                                            >
                                              {attr}
                                            </span>
                                          )
                                        )}
                                      </div>
                                    )}
                                </>
                              ) : (
                                <span className="bg-blue-600 text-white px-3 py-1 rounded text-xs font-bold">
                                  {item.score.toFixed(2)}
                                </span>
                              )}
                            </div>
                          </td>
                        )}
                        <td className="px-4 py-4">
                          <div
                            className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center cursor-pointer hover:bg-gray-200 hover:shadow-md transition-all duration-150"
                            onClick={() => handleRowClick(product)}
                            title="Click to view details"
                          >
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
                        {/* Alternative Product column - only show in regular browse mode */}
                        {!isSearchMode && (
                          <td className="px-4 py-4 text-sm">
                            {(() => {
                              const altData =
                                alternativesMap?.[product.wise_item_number];
                              if (!altData)
                                return <span className="text-gray-400">—</span>;

                              // Handle both old format (string) and new format (object)
                              const altWiseItemNumber =
                                typeof altData === "string"
                                  ? altData
                                  : altData.wise_item_number;
                              const matchScore =
                                typeof altData === "string"
                                  ? 0
                                  : altData.match_score || 0;
                              const varyingAttrs =
                                typeof altData === "string"
                                  ? []
                                  : altData.varying_attributes || [];

                              if (!altWiseItemNumber)
                                return <span className="text-gray-400">—</span>;

                              const getColor = (score) => {
                                if (score === 100) return "#22c55e";
                                if (score >= 75) return "#22c55e";
                                if (score >= 50) return "#eab308";
                                return "#f97316";
                              };

                              return (
                                <div className="flex items-start gap-3">
                                  {/* Progress Ring */}
                                  <div className="flex-shrink-0">
                                    <svg
                                      className="w-10 h-10"
                                      viewBox="0 0 36 36"
                                    >
                                      {/* Background circle */}
                                      <circle
                                        cx="18"
                                        cy="18"
                                        r="15.5"
                                        fill="none"
                                        stroke="#e5e7eb"
                                        strokeWidth="3"
                                      />
                                      {/* Progress circle */}
                                      <circle
                                        cx="18"
                                        cy="18"
                                        r="15.5"
                                        fill="none"
                                        stroke={getColor(matchScore)}
                                        strokeWidth="3"
                                        strokeLinecap="round"
                                        strokeDasharray={`${
                                          matchScore * 0.9738
                                        } 97.38`}
                                        transform="rotate(-90 18 18)"
                                      />
                                      {/* Score text */}
                                      <text
                                        x="18"
                                        y="18"
                                        textAnchor="middle"
                                        dominantBaseline="central"
                                        fontSize="9"
                                        fontWeight="bold"
                                        fill={getColor(matchScore)}
                                      >
                                        {matchScore}
                                      </text>
                                    </svg>
                                  </div>
                                  {/* Alternative details */}
                                  <div className="flex flex-col gap-1">
                                    <button
                                      onClick={() =>
                                        onAlternativeClick?.(altWiseItemNumber)
                                      }
                                      className="text-blue-600 hover:text-blue-800 hover:underline font-medium text-left"
                                      title="Click to search for this product"
                                    >
                                      {altWiseItemNumber}
                                    </button>
                                    {varyingAttrs.length > 0 && (
                                      <div className="text-xs text-gray-500">
                                        <span className="font-medium">
                                          Differs:{" "}
                                        </span>
                                        {varyingAttrs.join(", ")}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })()}
                          </td>
                        )}
                        {/* Actions column - Like/Dislike buttons and 3-dot menu for similar products */}
                        {isSearchMode && isHybridSearch && (
                          <td className="px-2 py-4 relative">
                            {showActionMenu && (
                              <div
                                className={`flex items-center gap-1 transition-opacity duration-150 ${
                                  hoveredRowId === productId ||
                                  menuOpenId === productId
                                    ? "opacity-100"
                                    : "opacity-0 group-hover:opacity-100"
                                }`}
                              >
                                {/* Like button */}
                                <button
                                  onClick={() =>
                                    handleFeedback(
                                      product.wise_item_number,
                                      "like"
                                    )
                                  }
                                  disabled={
                                    feedbackLoading[
                                      `${product.wise_item_number}-like`
                                    ]
                                  }
                                  className="flex items-center gap-0.5 p-1 rounded text-xs text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-50"
                                  title="Like this match"
                                >
                                  {feedbackLoading[
                                    `${product.wise_item_number}-like`
                                  ] ? (
                                    <div className="w-3.5 h-3.5 border border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                                  ) : (
                                    <svg
                                      className="w-4 h-4"
                                      fill="none"
                                      stroke="currentColor"
                                      strokeWidth={1.5}
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M6.633 10.25c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 0 1 2.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 0 0 .322-1.672V2.75a.75.75 0 0 1 .75-.75 2.25 2.25 0 0 1 2.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282m0 0h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 0 1-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 0 0-1.423-.23H5.904m10.598-9.75H14.25M5.904 18.5c.083.205.173.405.27.602.197.4-.078.898-.523.898h-.908c-.889 0-1.713-.518-1.972-1.368a12 12 0 0 1-.521-3.507c0-1.553.295-3.036.831-4.398C3.387 9.953 4.167 9.5 5 9.5h1.053c.472 0 .745.556.5.96a8.958 8.958 0 0 0-1.302 4.665c0 1.194.232 2.333.654 3.375Z"
                                      />
                                    </svg>
                                  )}
                                  <span>{item.likes || 0}</span>
                                </button>
                                {/* Dislike button */}
                                <button
                                  onClick={() =>
                                    handleFeedback(
                                      product.wise_item_number,
                                      "dislike"
                                    )
                                  }
                                  disabled={
                                    feedbackLoading[
                                      `${product.wise_item_number}-dislike`
                                    ]
                                  }
                                  className="flex items-center gap-0.5 p-1 rounded text-xs text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-50"
                                  title="Dislike this match"
                                >
                                  {feedbackLoading[
                                    `${product.wise_item_number}-dislike`
                                  ] ? (
                                    <div className="w-3.5 h-3.5 border border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                                  ) : (
                                    <svg
                                      className="w-4 h-4"
                                      fill="none"
                                      stroke="currentColor"
                                      strokeWidth={1.5}
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M7.498 15.25H4.372c-1.026 0-1.945-.694-2.054-1.715a12.137 12.137 0 0 1-.068-1.285c0-2.848.992-5.464 2.649-7.521C5.287 4.247 5.886 4 6.504 4h4.016a4.5 4.5 0 0 1 1.423.23l3.114 1.04a4.5 4.5 0 0 0 1.423.23h1.294M7.498 15.25c.618 0 .991.724.725 1.282A7.471 7.471 0 0 0 7.5 19.75 2.25 2.25 0 0 0 9.75 22a.75.75 0 0 0 .75-.75v-.633c0-.573.11-1.14.322-1.672.304-.76.93-1.33 1.653-1.715a9.04 9.04 0 0 0 2.86-2.4c.498-.634 1.226-1.08 2.032-1.08h.384m-10.253 1.5H9.7m8.075-9.75c.01.05.027.1.05.148.593 1.2.925 2.55.925 3.977 0 1.487-.36 2.89-.999 4.125m.023-8.25c-.076-.365.183-.75.575-.75h.908c.889 0 1.713.518 1.972 1.368.339 1.11.521 2.287.521 3.507 0 1.553-.295 3.036-.831 4.398-.306.774-1.086 1.227-1.918 1.227h-1.053c-.472 0-.745-.556-.5-.96a8.95 8.95 0 0 0 .303-.54"
                                      />
                                    </svg>
                                  )}
                                  <span>{item.dislikes || 0}</span>
                                </button>
                                {/* 3-dot menu */}
                                {/* <button
                                  onClick={(e) => handleMenuClick(productId, e)}
                                  className="p-1 rounded hover:bg-gray-200 text-gray-400 hover:text-gray-600"
                                  title="More actions"
                                >
                                  <svg
                                    className="w-4 h-4"
                                    fill="currentColor"
                                    viewBox="0 0 24 24"
                                  >
                                    <circle cx="12" cy="5" r="2" />
                                    <circle cx="12" cy="12" r="2" />
                                    <circle cx="12" cy="19" r="2" />
                                  </svg>
                                </button>  */}
                                {/* Dropdown menu */}
                                {menuOpenId === productId && (
                                  <div
                                    ref={menuRef}
                                    className="absolute right-0 top-8 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[120px]"
                                  >
                                    <button
                                      onClick={(e) =>
                                        handleReportClick(productId, e)
                                      }
                                      className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-2"
                                    >
                                      <svg
                                        className="w-4 h-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                      >
                                        <path
                                          strokeLinecap="round"
                                          strokeLinejoin="round"
                                          strokeWidth={2}
                                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                        />
                                      </svg>
                                      Remove
                                    </button>
                                  </div>
                                )}
                              </div>
                            )}
                          </td>
                        )}
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
