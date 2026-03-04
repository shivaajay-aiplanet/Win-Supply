import { useState, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function ProductDetailModal({ product, isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState("all");
  const [iofOnly, setIofOnly] = useState(false);
  const [vendorReferences, setVendorReferences] = useState([]);
  const [vendorLoading, setVendorLoading] = useState(false);

  const tabs = [
    { id: "all", label: "All" },
    { id: "wss", label: "WSS Locations" },
    { id: "local", label: "Local Companies" },
    { id: "preferred", label: "Preferred Companies", icon: "★" },
  ];

  // Single company location data - Winsupply Regional Distribution Center
  const locationData = [
    {
      companyNumber: "00102",
      companyName: "Winsupply Regional Distribution Center",
      milesAway: 12,
      availableToSell: 17,
      iov: 27,
      onHand: 1,
      onSO: 2,
      onBO: 0,
      onPO: 0,
      isPreferred: true,
    },
  ];

  // Fetch vendor cross references when modal opens
  useEffect(() => {
    if (isOpen && product?.wise_item_number) {
      fetchVendorCrossReferences(product.wise_item_number);
    }
    // Reset state when modal closes
    if (!isOpen) {
      setVendorReferences([]);
    }
  }, [isOpen, product?.wise_item_number]);

  // Fetch vendor cross references from API
  const fetchVendorCrossReferences = async (wiseItemNumber) => {
    setVendorLoading(true);
    try {
      // First, try to get cross-reference alternatives from the database
      const altResponse = await fetch(
        `${API_BASE_URL}/search/cross-reference/alternatives`
      );

      if (altResponse.ok) {
        const altData = await altResponse.json();

        // Check if we have alternatives for this wise_item_number
        if (altData.alternatives && altData.alternatives[wiseItemNumber]) {
          // We have cross-reference data, now fetch product details for similar items
          const similarProducts = await fetchSimilarProductDetails(
            wiseItemNumber
          );
          if (similarProducts.length > 0) {
            setVendorReferences(similarProducts);
            setVendorLoading(false);
            return;
          }
        }
      }

      // If no cross-reference data found, perform hybrid search
      await performHybridSearch(wiseItemNumber);
    } catch (error) {
      console.error("Error fetching vendor cross references:", error);
      // Fallback to hybrid search on error
      await performHybridSearch(wiseItemNumber);
    }
  };

  // Fetch similar product details from cross-reference
  const fetchSimilarProductDetails = async (wiseItemNumber) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/search/wise-item?wise_item_number=${encodeURIComponent(
          wiseItemNumber
        )}&top_k=20`
      );

      if (response.ok) {
        const data = await response.json();
        if (data.results && data.results.length > 0) {
          // Skip the first result (it's the source product itself) and map the rest
          return data.results.slice(1).map((item) => ({
            wiseItemNumber: item.wise_item_number || "N/A",
            vendor: item.brand_name || item.preferred_supplier || "N/A",
            matchScore: item.match_score || 0,
            varyingAttributes: item.varying_attributes || [],
          }));
        }
      }
      return [];
    } catch (error) {
      console.error("Error fetching similar product details:", error);
      return [];
    }
  };

  // Perform hybrid + LLM search for similar products
  const performHybridSearch = async (wiseItemNumber) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/search/wise-item?wise_item_number=${encodeURIComponent(
          wiseItemNumber
        )}&top_k=20`
      );

      if (response.ok) {
        const data = await response.json();
        if (data.results && data.results.length > 0) {
          // Skip the first result (source product) and map the rest
          const references = data.results.slice(1).map((item) => ({
            wiseItemNumber: item.wise_item_number || "N/A",
            vendor: item.brand_name || item.preferred_supplier || "N/A",
            matchScore: item.match_score || 0,
            varyingAttributes: item.varying_attributes || [],
          }));
          setVendorReferences(references);
        } else {
          setVendorReferences([]);
        }
      } else {
        setVendorReferences([]);
      }
    } catch (error) {
      console.error("Error performing hybrid search:", error);
      setVendorReferences([]);
    } finally {
      setVendorLoading(false);
    }
  };

  if (!isOpen || !product) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Item Availability
            </h2>
            <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
              <span>
                <span className="font-medium text-gray-700">Company:</span> Win
                Supply HQ
              </span>
              <span>
                <span className="font-medium text-gray-700">Company ID:</span>{" "}
                0001
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <div className="flex gap-6">
            {/* Left Section - Product Info & Locations */}
            <div className="flex-1">
              {/* Product Header */}
              <div className="flex gap-4 mb-6">
                {/* Product Image */}
                <div className="w-24 h-24 bg-gray-100 rounded flex items-center justify-center flex-shrink-0">
                  <svg
                    className="w-12 h-12 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                    />
                  </svg>
                </div>

                {/* Product Details */}
                <div className="flex-1">
                  <div className="flex items-start gap-2">
                    <div>
                      <p className="text-sm font-semibold text-gray-800">
                        {product.brand_name || "NIBCO"}
                      </p>
                      <p className="text-sm text-gray-600">
                        {product.win_item_name ||
                          product.mainframe_description ||
                          "N/A"}
                      </p>
                    </div>
                    <button className="text-blue-600 hover:text-blue-800">
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
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Product Specs */}
                <div className="border-l border-gray-200 pl-4 grid grid-cols-3 gap-x-6 gap-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">WISE Item Number</span>
                    <p className="font-medium flex items-center gap-1">
                      {product.wise_item_number || "N/A"}{" "}
                      <button className="text-gray-400 hover:text-gray-600">
                        <svg
                          className="w-3 h-3"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                          />
                        </svg>
                      </button>
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">Weight</span>
                    <p className="font-medium">{product.weight || "N/A"}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Catalog Number</span>
                    <p className="font-medium">
                      {product.catalog_number || "N/A"}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">Order Number</span>
                    <p className="font-medium">
                      {product.order_number || "N/A"}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">UPC</span>
                    <p className="font-medium">{product.upc || "N/A"}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Model Number</span>
                    <p className="font-medium">
                      {product.model_number || "N/A"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <div className="flex items-center gap-1">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap inline-flex items-center ${
                        activeTab === tab.id
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {tab.icon && <span className="mr-1">{tab.icon}</span>}
                      {tab.label}
                    </button>
                  ))}
                </div>
                <span className="text-sm text-gray-500 ml-4">
                  Available at 780 Locations
                </span>
                <label className="flex items-center gap-2 ml-auto text-sm cursor-pointer">
                  <span>IOV Only</span>
                  <div
                    className={`relative w-10 h-5 rounded-full transition-colors cursor-pointer ${
                      iofOnly ? "bg-blue-600" : "bg-gray-300"
                    }`}
                    onClick={() => setIofOnly(!iofOnly)}
                  >
                    <div
                      className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                        iofOnly ? "translate-x-5" : "translate-x-0.5"
                      }`}
                    ></div>
                  </div>
                </label>
              </div>

              {/* Filter Inputs */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Company Name or Number
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder=""
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Address
                  </label>
                  <input
                    type="text"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Address, City, State, or Zip Code"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Miles Away
                  </label>
                  <select className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                    <option value="">Select</option>
                    <option value="10">Within 10 miles</option>
                    <option value="25">Within 25 miles</option>
                    <option value="50">Within 50 miles</option>
                    <option value="100">Within 100 miles</option>
                  </select>
                </div>
              </div>

              {/* Location Table */}
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-600"></th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        Company Number <span className="text-gray-400">↑↓</span>
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        Company Name <span className="text-gray-400">↑↓</span>
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        Miles Away <span className="text-gray-400">↑↓</span>
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        Available to Sell
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        IOV
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        On Hand
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        On S.O.
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        On B.O.
                      </th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">
                        On P.O.
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {locationData.map((loc, idx) => (
                      <tr
                        key={idx}
                        className="border-b border-gray-100 hover:bg-blue-50"
                      >
                        <td className="px-3 py-3">
                          {loc.isPreferred ? (
                            <span className="text-blue-600">★</span>
                          ) : (
                            <span className="text-gray-300">☆</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-gray-700">
                          {loc.companyNumber}
                        </td>
                        <td className="px-3 py-3 text-blue-600 hover:underline cursor-pointer">
                          {loc.companyName}
                        </td>
                        <td className="px-3 py-3 text-gray-700">
                          {loc.milesAway}
                        </td>
                        <td className="px-3 py-3 text-gray-700">
                          {loc.availableToSell}
                        </td>
                        <td className="px-3 py-3 text-gray-700">{loc.iov}</td>
                        <td className="px-3 py-3 text-gray-700">
                          {loc.onHand}
                        </td>
                        <td className="px-3 py-3 text-gray-700">{loc.onSO}</td>
                        <td className="px-3 py-3 text-gray-700">{loc.onBO}</td>
                        <td className="px-3 py-3 text-gray-700">{loc.onPO}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right Section - Vendor Part Cross References */}
            <div className="w-80 border-l border-gray-200 pl-6 flex-shrink-0 flex flex-col max-h-full">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex-shrink-0">
                Vendor Part Cross References
              </h3>

              {vendorLoading ? (
                <div className="flex-1 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b border-gray-200 sticky top-0 bg-white">
                      <tr>
                        <th className="pb-2 text-left font-medium text-gray-600">
                          WISE Item Number
                        </th>
                        <th className="pb-2 text-left font-medium text-gray-600">
                          Vendors
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...Array(5)].map((_, idx) => (
                        <tr key={idx} className="border-b border-gray-100">
                          <td className="py-3">
                            <div className="flex items-start gap-3">
                              {/* Skeleton Progress Ring */}
                              <div className="w-10 h-10 bg-gray-200 rounded-full animate-pulse flex-shrink-0"></div>
                              {/* Skeleton details */}
                              <div className="flex flex-col gap-2">
                                <div className="h-4 bg-gray-200 rounded w-24 animate-pulse"></div>
                                <div className="h-3 bg-gray-200 rounded w-32 animate-pulse"></div>
                              </div>
                            </div>
                          </td>
                          <td className="py-3">
                            <div className="h-4 bg-gray-200 rounded w-20 animate-pulse"></div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : vendorReferences.length > 0 ? (
                <div className="flex-1 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b border-gray-200 sticky top-0 bg-white">
                      <tr>
                        <th className="pb-2 text-left font-medium text-gray-600">
                          WISE Item Number
                        </th>
                        <th className="pb-2 text-left font-medium text-gray-600">
                          Vendors
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {vendorReferences.map((ref, idx) => {
                        const getColor = (score) => {
                          if (score >= 90) return "#22c55e"; // Green for 90+
                          if (score >= 80) return "#f97316"; // Orange for 80-89
                          return "#ef4444"; // Red for below 80
                        };
                        const scoreColor = getColor(ref.matchScore);

                        return (
                          <tr
                            key={idx}
                            className="border-b border-gray-100 hover:bg-blue-50"
                          >
                            <td className="py-3">
                              <div className="flex items-start gap-3">
                                {/* Progress Ring - same as Alternative Product UI */}
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
                                      stroke={scoreColor}
                                      strokeWidth="3"
                                      strokeLinecap="round"
                                      strokeDasharray={`${
                                        ref.matchScore * 0.9738
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
                                      fill={scoreColor}
                                    >
                                      {ref.matchScore}
                                    </text>
                                  </svg>
                                </div>
                                {/* Alternative details */}
                                <div className="flex flex-col gap-1">
                                  <a
                                    href="#"
                                    className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                                  >
                                    {ref.wiseItemNumber}
                                  </a>
                                  {ref.varyingAttributes &&
                                    ref.varyingAttributes.length > 0 && (
                                      <div className="text-xs text-gray-500">
                                        <span className="font-medium">
                                          Differs:{" "}
                                        </span>
                                        {ref.varyingAttributes.join(", ")}
                                      </div>
                                    )}
                                </div>
                              </div>
                            </td>
                            <td className="py-3 text-gray-700">{ref.vendor}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-sm">No similar products found</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductDetailModal;
