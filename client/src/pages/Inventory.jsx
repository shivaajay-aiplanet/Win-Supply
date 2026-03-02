import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import SearchBar from "../components/SearchBar";
import RefineSearch from "../components/RefineSearch";
import ProductTable from "../components/ProductTable";

const API_BASE_URL = "http://localhost:8000/api";

function Inventory() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
    total_count: 0,
    total_pages: 0,
    has_next: false,
    has_previous: false,
  });

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const topK = 20; // Fixed value for search results limit
  const [exactMatchId, setExactMatchId] = useState(null);
  const [searchType, setSearchType] = useState("wise_item_number"); // "all_fields" or "wise_item_number"
  const [isHybridSearch, setIsHybridSearch] = useState(false); // Track if using hybrid search
  const [showScores, setShowScores] = useState(false); // Toggle for showing/hiding search scores
  const [notFound, setNotFound] = useState(false); // Track if item was not found
  const [notFoundItemNumber, setNotFoundItemNumber] = useState(""); // Store the item number that wasn't found

  // Sort and Filter state
  const [sortBy, setSortBy] = useState("relevance");
  const [brandFilter, setBrandFilter] = useState("");

  // Alternatives state
  const [alternativesMap, setAlternativesMap] = useState({});

  // Fetch products from API
  const fetchProducts = async (page = 1) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/inventory/products?page=${page}&page_size=10`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setProducts(data.products);
      setPagination(data.pagination);
    } catch (err) {
      setError(err.message);
      console.error("Error fetching products:", err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch alternatives from cross-reference table
  const fetchAlternatives = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/search/cross-reference/alternatives`
      );

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.alternatives) {
          setAlternativesMap(data.alternatives);
        }
      }
    } catch (err) {
      console.error("Error fetching alternatives:", err);
    }
  };

  // Search products using BM25 or Hybrid Search
  const searchProducts = async (query) => {
    if (!query.trim()) {
      return;
    }

    setSearchLoading(true);
    setError(null);
    setNotFound(false);
    setNotFoundItemNumber("");

    try {
      let response;
      let data;

      // Choose endpoint based on search type
      if (searchType === "wise_item_number") {
        // Hybrid search endpoint for WISE item number
        response = await fetch(
          `${API_BASE_URL}/search/wise-item?wise_item_number=${encodeURIComponent(
            query
          )}&top_k=${topK}`
        );

        if (!response.ok) {
          if (response.status === 404) {
            // Handle 404 specifically for "not found" case
            setNotFound(true);
            setNotFoundItemNumber(query);
            setIsSearchMode(true);
            setSearchResults(null);
            return;
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        data = await response.json();

        // Transform hybrid search results to match expected format
        const transformedData = {
          query: data.query_text || query,
          wise_item_number: data.wise_item_number,
          source_product: data.source_product,
          search_stats: data.search_stats,
          total_hits: data.total_results,
          returned_count: data.total_results,
          results: data.results || [],
          is_hybrid: true,
        };

        setSearchResults(transformedData);
        setIsHybridSearch(true);
        setIsSearchMode(true);

        // For hybrid search, the top result is already the best match
        if (transformedData.results.length > 0) {
          setExactMatchId(transformedData.results[0].id);
        }
      } else {
        // Regular BM25 keyword search
        response = await fetch(
          `${API_BASE_URL}/search?q=${encodeURIComponent(query)}&top_k=${topK}`
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        data = await response.json();
        setSearchResults(data);
        setIsHybridSearch(false);
        setIsSearchMode(true);

        // Find exact match (highest score or exact text match)
        if (data.results && data.results.length > 0) {
          const topResult = data.results[0];
          // Consider it an exact match if score is very high or name matches exactly
          const isExactMatch =
            topResult.score > 20 ||
            topResult.document.win_item_name?.toLowerCase() ===
              query.toLowerCase() ||
            topResult.document.mainframe_description?.toLowerCase() ===
              query.toLowerCase();

          if (isExactMatch) {
            setExactMatchId(topResult.id);
          } else {
            setExactMatchId(null);
          }
        }
      }
    } catch (err) {
      setError(err.message);
      console.error("Error searching products:", err);
    } finally {
      setSearchLoading(false);
    }
  };

  // Handle search button click
  const handleSearch = () => {
    searchProducts(searchQuery);
  };

  // Handle reset button click
  const handleReset = () => {
    setSearchQuery("");
    setSearchResults(null);
    setIsSearchMode(false);
    setIsHybridSearch(false);
    setExactMatchId(null);
    setError(null);
    setSearchType("wise_item_number");
    setNotFound(false);
    setNotFoundItemNumber("");
    fetchProducts(1);
  };

  // Toggle search scores visibility
  const toggleScores = () => {
    setShowScores((prev) => !prev);
  };

  // Apply sorting to search results or products
  const applySorting = (items, inSearchMode) => {
    if (!items || items.length === 0) return [];

    const sorted = [...items];

    switch (sortBy) {
      case "name_asc":
        sorted.sort((a, b) => {
          const doc1 = inSearchMode ? a.document : a;
          const doc2 = inSearchMode ? b.document : b;
          const nameA = (doc1.win_item_name || "").toLowerCase();
          const nameB = (doc2.win_item_name || "").toLowerCase();
          return nameA.localeCompare(nameB);
        });
        break;
      case "name_desc":
        sorted.sort((a, b) => {
          const doc1 = inSearchMode ? a.document : a;
          const doc2 = inSearchMode ? b.document : b;
          const nameA = (doc1.win_item_name || "").toLowerCase();
          const nameB = (doc2.win_item_name || "").toLowerCase();
          return nameB.localeCompare(nameA);
        });
        break;
      case "brand_asc":
        sorted.sort((a, b) => {
          const doc1 = inSearchMode ? a.document : a;
          const doc2 = inSearchMode ? b.document : b;
          const brandA = (doc1.brand_name || "").toLowerCase();
          const brandB = (doc2.brand_name || "").toLowerCase();
          return brandA.localeCompare(brandB);
        });
        break;
      case "brand_desc":
        sorted.sort((a, b) => {
          const doc1 = inSearchMode ? a.document : a;
          const doc2 = inSearchMode ? b.document : b;
          const brandA = (doc1.brand_name || "").toLowerCase();
          const brandB = (doc2.brand_name || "").toLowerCase();
          return brandB.localeCompare(brandA);
        });
        break;
      case "relevance":
      default:
        // Keep original order (relevance for search, default for browse)
        break;
    }

    return sorted;
  };

  // Apply filtering to search results or products
  const applyFiltering = (items, inSearchMode) => {
    if (!items || items.length === 0) return [];

    let filtered = [...items];

    // Apply brand filter (exact match)
    if (brandFilter && brandFilter.trim() !== "") {
      filtered = filtered.filter((item) => {
        const doc = inSearchMode ? item.document : item;
        const brandName = doc.brand_name || "";
        return brandName === brandFilter;
      });
    }

    return filtered;
  };

  // Extract unique brands from search results or products
  const getAvailableBrands = () => {
    const brands = new Set();

    if (isSearchMode && searchResults?.results) {
      // Handle search results (both hybrid and regular)
      searchResults.results.forEach((item) => {
        // For hybrid search, brand is directly on item
        // For regular search, brand is on item.document
        const brandName = isHybridSearch
          ? item.brand_name
          : item.document?.brand_name;
        if (brandName && brandName.trim() !== "") {
          brands.add(brandName);
        }
      });
    } else if (products && products.length > 0) {
      // Handle browse mode - get brands from products
      products.forEach((product) => {
        if (product.brand_name && product.brand_name.trim() !== "") {
          brands.add(product.brand_name);
        }
      });
    }

    return Array.from(brands).sort();
  };

  // Get processed search results (maintains search result structure with scores)
  const getProcessedSearchResults = () => {
    if (!searchResults) return null;

    let results = searchResults.results || [];

    // Apply filtering first
    results = applyFiltering(results, true);

    // Then apply sorting
    results = applySorting(results, true);

    return {
      ...searchResults,
      results: results,
      returned_count: results.length,
    };
  };

  // Get processed products for non-search mode
  const getProcessedProducts = () => {
    let processedProducts = products;

    // Apply filtering first
    processedProducts = applyFiltering(processedProducts, false);

    // Then apply sorting
    processedProducts = applySorting(processedProducts, false);

    return processedProducts;
  };

  // Handle deleting a match from cross-reference
  const handleDeleteMatch = async (
    sourceWiseItemNumber,
    matchedWiseItemNumber
  ) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/search/cross-reference/delete-match?source_wise_item_number=${encodeURIComponent(
          sourceWiseItemNumber
        )}&matched_wise_item_number=${encodeURIComponent(
          matchedWiseItemNumber
        )}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Remove the deleted match from search results
      if (searchResults && searchResults.results) {
        const updatedResults = searchResults.results.filter(
          (item) => item.wise_item_number !== matchedWiseItemNumber
        );
        setSearchResults({
          ...searchResults,
          results: updatedResults,
          returned_count: updatedResults.length,
        });
      }
    } catch (error) {
      console.error("Error deleting match:", error);
      throw error;
    }
  };

  // Handle like/dislike feedback for a match
  const handleFeedback = async (
    sourceWiseItemNumber,
    matchedWiseItemNumber,
    feedbackType
  ) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/search/cross-reference/feedback?source_wise_item_number=${encodeURIComponent(
          sourceWiseItemNumber
        )}&matched_wise_item_number=${encodeURIComponent(
          matchedWiseItemNumber
        )}&feedback_type=${encodeURIComponent(feedbackType)}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // If the match was removed due to too many dislikes, remove from results
      if (data.removed) {
        if (searchResults && searchResults.results) {
          const updatedResults = searchResults.results.filter(
            (item) => item.wise_item_number !== matchedWiseItemNumber
          );
          setSearchResults({
            ...searchResults,
            results: updatedResults,
            returned_count: updatedResults.length,
          });
        }
      } else {
        // Update the like/dislike counts in the search results
        if (searchResults && searchResults.results) {
          const updatedResults = searchResults.results.map((item) => {
            if (item.wise_item_number === matchedWiseItemNumber) {
              return {
                ...item,
                likes: data.likes,
                dislikes: data.dislikes,
              };
            }
            return item;
          });
          setSearchResults({
            ...searchResults,
            results: updatedResults,
          });
        }
      }
    } catch (error) {
      console.error("Error submitting feedback:", error);
      throw error;
    }
  };

  // Fetch products and alternatives on component mount
  useEffect(() => {
    fetchProducts(1);
    fetchAlternatives();
  }, []);

  // Handle page navigation
  const handlePreviousPage = () => {
    if (pagination.has_previous) {
      fetchProducts(pagination.page - 1);
    }
  };

  const handleNextPage = () => {
    if (pagination.has_next) {
      fetchProducts(pagination.page + 1);
    }
  };

  return (
    <div className="h-full w-full bg-gradient-to-br from-gray-50 via-blue-50 to-gray-100 flex flex-col overflow-hidden">
      {/* Header */}
      <Header showScores={showScores} toggleScores={toggleScores} />

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
        <div className="flex justify-between items-center">
          <div className="flex gap-0">
            <button className="px-6 py-4 text-sm font-semibold text-blue-600 border-b-2 border-blue-600 bg-blue-50">
              Products
            </button>
            <button className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-colors">
              Customers
            </button>
            <button className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-colors">
              Locations
            </button>
            <button className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-colors">
              Vendors
            </button>
          </div>
          <div className="pr-6">
            <button
              onClick={() => navigate("/bulk-upload")}
              className="px-5 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Bulk Upload
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        <div className="pt-6 pb-4 px-6 flex-shrink-0">
          {/* Title Bar */}
          <div className="flex items-center gap-4 mb-4">
            <h1 className="text-2xl font-semibold text-gray-800">
              Inventory Search
            </h1>
          </div>

          {/* Search Bar */}
          <SearchBar
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            searchType={searchType}
            setSearchType={setSearchType}
            handleSearch={handleSearch}
            handleReset={handleReset}
            searchLoading={searchLoading}
          />
        </div>

        <div className="flex-1 flex gap-5 overflow-hidden pb-6 px-6 min-h-0">
          {/* Sidebar */}
          <RefineSearch
            sortBy={sortBy}
            setSortBy={setSortBy}
            brandFilter={brandFilter}
            setBrandFilter={setBrandFilter}
            availableBrands={getAvailableBrands()}
          />

          {/* Products Table */}
          <ProductTable
            loading={loading}
            searchLoading={searchLoading}
            error={error}
            isSearchMode={isSearchMode}
            searchResults={getProcessedSearchResults()}
            products={getProcessedProducts()}
            exactMatchId={exactMatchId}
            isHybridSearch={isHybridSearch}
            pagination={pagination}
            handlePreviousPage={handlePreviousPage}
            handleNextPage={handleNextPage}
            showScores={showScores}
            sourceWiseItemNumber={searchResults?.wise_item_number}
            onDeleteMatch={handleDeleteMatch}
            onFeedback={handleFeedback}
            alternativesMap={alternativesMap}
            notFound={notFound}
            notFoundItemNumber={notFoundItemNumber}
            onAlternativeClick={(wiseItemNumber) => {
              setSearchQuery(wiseItemNumber);
              setSearchType("wise_item_number");
              searchProducts(wiseItemNumber);
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default Inventory;
