import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import {
  FiUploadCloud,
  FiFile,
  FiX,
  FiCheck,
  FiAlertCircle,
  FiLoader,
  FiSearch,
  FiSave,
  FiChevronDown,
  FiChevronUp,
  FiRotateCcw,
} from "react-icons/fi";
import * as XLSX from "xlsx";

const API_BASE_URL = "http://localhost:8000/api";

// Required headers in the Excel file
const REQUIRED_HEADERS = [
  "Brand Name",
  "Wise Item No",
  "Catalog No",
  "Mainframe Description",
  "Win Item Name",
];

function BulkUpload() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // File upload state
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [fileError, setFileError] = useState(null);

  // Data state
  const [parsedData, setParsedData] = useState([]);
  const [showParsedData, setShowParsedData] = useState(false);

  // Cross-reference state
  const [crossRefResults, setCrossRefResults] = useState([]);
  const [crossRefLoading, setCrossRefLoading] = useState(false);
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0);
  const [crossRefError, setCrossRefError] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});
  const [excludedMatches, setExcludedMatches] = useState({}); // Track removed matches per source product

  // Save state
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);

  // Validate headers in the uploaded file
  const validateHeaders = (headers) => {
    const normalizedHeaders = headers.map((h) =>
      h?.toString().trim().toLowerCase()
    );
    const missingHeaders = REQUIRED_HEADERS.filter(
      (required) => !normalizedHeaders.includes(required.toLowerCase())
    );
    return missingHeaders;
  };

  // Parse Excel file
  const parseExcelFile = useCallback((file) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: "array" });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        if (jsonData.length < 2) {
          setFileError("File is empty or contains only headers");
          return;
        }

        const headers = jsonData[0];
        const missingHeaders = validateHeaders(headers);

        if (missingHeaders.length > 0) {
          setFileError(
            `Missing required columns: ${missingHeaders.join(", ")}`
          );
          return;
        }

        // Map headers to normalized keys
        const headerMap = {};
        headers.forEach((header, index) => {
          const normalized = header?.toString().trim().toLowerCase();
          if (normalized === "brand name") headerMap[index] = "brand_name";
          else if (normalized === "wise item no")
            headerMap[index] = "wise_item_number";
          else if (normalized === "catalog no")
            headerMap[index] = "catalog_number";
          else if (normalized === "mainframe description")
            headerMap[index] = "mainframe_description";
          else if (normalized === "win item name")
            headerMap[index] = "win_item_name";
        });

        // Parse rows
        const rows = jsonData.slice(1).map((row, rowIndex) => {
          const item = { id: rowIndex + 1 };
          Object.entries(headerMap).forEach(([colIndex, key]) => {
            item[key] = row[parseInt(colIndex)]?.toString() || "";
          });
          return item;
        });

        // Filter out empty rows
        const validRows = rows.filter(
          (row) => row.wise_item_number || row.win_item_name || row.brand_name
        );

        setParsedData(validRows);
        setFileError(null);
        setShowParsedData(false);
        setCrossRefResults([]);
        setSaveSuccess(false);
      } catch (error) {
        console.error("Error parsing file:", error);
        setFileError(
          "Failed to parse file. Please ensure it's a valid Excel file."
        );
      }
    };

    reader.onerror = () => {
      setFileError("Failed to read file");
    };

    reader.readAsArrayBuffer(file);
  }, []);

  // Handle file drop
  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        const extension = droppedFile.name.split(".").pop().toLowerCase();
        if (["csv", "xlsx", "xls"].includes(extension)) {
          setFile(droppedFile);
          setFileError(null);
          parseExcelFile(droppedFile);
        } else {
          setFileError(
            "Invalid file type. Please upload CSV, XLSX, or XLS file."
          );
        }
      }
    },
    [parseExcelFile]
  );

  // Handle drag events
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  // Handle file input change
  const handleFileInput = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      const extension = selectedFile.name.split(".").pop().toLowerCase();
      if (["csv", "xlsx", "xls"].includes(extension)) {
        setFile(selectedFile);
        setFileError(null);
        parseExcelFile(selectedFile);
      } else {
        setFileError(
          "Invalid file type. Please upload CSV, XLSX, or XLS file."
        );
      }
    }
  };

  // Clear file
  const clearFile = () => {
    setFile(null);
    setParsedData([]);
    setShowParsedData(false);
    setFileError(null);
    setCrossRefResults([]);
    setSaveSuccess(false);
    setSaveError(null);
    setExcludedMatches({});
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Handle Proceed button - show parsed data
  const handleProceed = () => {
    setShowParsedData(true);
  };

  // Upload state
  const [uploadStatus, setUploadStatus] = useState(null);

  // Run cross-reference search for all products
  const handleCrossReference = async () => {
    if (parsedData.length === 0) return;

    setCrossRefLoading(true);
    setCrossRefError(null);
    setCrossRefResults([]);
    setExpandedRows({});
    setExcludedMatches({});
    setUploadStatus("uploading");

    // Step 1: Upload products to inventory first
    try {
      const uploadPayload = {
        products: parsedData.map((product) => ({
          wise_item_number: product.wise_item_number,
          win_item_name: product.win_item_name,
          brand_name: product.brand_name,
          catalog_number: product.catalog_number,
          mainframe_description: product.mainframe_description,
        })),
      };

      const uploadResponse = await fetch(
        `${API_BASE_URL}/bulk-upload/upload-products`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(uploadPayload),
        }
      );

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        throw new Error(
          errorData.detail || "Failed to upload products to inventory"
        );
      }

      const uploadResult = await uploadResponse.json();
      console.log("Upload result:", uploadResult);
      setUploadStatus("uploaded");

      // Small delay to ensure OpenSearch has indexed the products
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } catch (error) {
      console.error("Error uploading products:", error);
      setCrossRefError(`Failed to upload products: ${error.message}`);
      setCrossRefLoading(false);
      setUploadStatus("error");
      return;
    }

    // Step 2: Run cross-reference search for each product
    setUploadStatus("searching");
    const results = [];

    for (let i = 0; i < parsedData.length; i++) {
      setCurrentSearchIndex(i);
      const product = parsedData[i];

      try {
        // Call the search API for each wise_item_number
        const response = await fetch(
          `${API_BASE_URL}/search/wise-item?wise_item_number=${encodeURIComponent(
            product.wise_item_number
          )}&top_k=10`
        );

        if (!response.ok) {
          // Check if it's a 404 (product not found) - treat as "no matches" instead of error
          if (response.status === 404) {
            const errorData = await response.json();
            results.push({
              sourceProduct: product,
              searchResults: [],
              sourceProductData: null,
              productFound: false,
              error: null, // Not an error, just no product found
              notFoundMessage:
                errorData.detail ||
                `Product not found: ${product.wise_item_number}`,
            });
          } else {
            throw new Error(`Search failed for ${product.wise_item_number}`);
          }
        } else {
          const data = await response.json();

          results.push({
            sourceProduct: product,
            searchResults: data.results || [],
            sourceProductData: data.source_product,
            productFound: data.product_found,
            error: null,
          });
        }
      } catch (error) {
        console.error(
          `Error searching for ${product.wise_item_number}:`,
          error
        );
        results.push({
          sourceProduct: product,
          searchResults: [],
          sourceProductData: null,
          productFound: false,
          error: error.message,
        });
      }

      // Update results incrementally
      setCrossRefResults([...results]);
    }

    setUploadStatus("complete");
    setCrossRefLoading(false);
  };

  // Toggle expanded row
  const toggleExpandRow = (index) => {
    setExpandedRows((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  // Handle removing/restoring a match
  const handleRemoveMatch = (sourceIndex, matchIndex) => {
    setExcludedMatches((prev) => {
      const updated = { ...prev };
      if (!updated[sourceIndex]) {
        updated[sourceIndex] = new Set();
      } else {
        // Create a new Set to ensure React detects the change
        updated[sourceIndex] = new Set(updated[sourceIndex]);
      }

      if (updated[sourceIndex].has(matchIndex)) {
        updated[sourceIndex].delete(matchIndex); // Restore
      } else {
        updated[sourceIndex].add(matchIndex); // Remove
      }

      // If the set is empty, remove it from the object
      if (updated[sourceIndex].size === 0) {
        delete updated[sourceIndex];
      }

      return updated;
    });
  };

  // Get active (non-removed) match count for a source
  const getActiveMatchCount = (sourceIndex, totalMatches) => {
    const excluded = excludedMatches[sourceIndex];
    if (!excluded || excluded.size === 0) return totalMatches;
    return totalMatches - excluded.size;
  };

  // Get total removed count across all sources
  const getTotalRemovedCount = () => {
    return Object.values(excludedMatches).reduce(
      (sum, set) => sum + set.size,
      0
    );
  };

  // Handle Save to database
  const handleSave = async () => {
    if (crossRefResults.length === 0) return;

    setSaveLoading(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      // Prepare data for saving, filtering out excluded matches
      const saveData = crossRefResults
        .map((result, sourceIdx) => {
          if (!result.productFound || !result.searchResults?.length) return null;

          const excludedSet = excludedMatches[sourceIdx] || new Set();

          // Filter out excluded matches
          const filteredMatches = result.searchResults
            .filter((_, matchIdx) => !excludedSet.has(matchIdx))
            .map((match) => ({
              r: `${match.wise_item_number || match.document?.wise_item_number}|${
                match.relevance_score
                  ? Math.round(match.relevance_score * 100)
                  : match.match_score || 50
              }|${(match.varying_attributes || []).join(",")}`,
            }));

          // Only include if there are matches left after filtering
          return filteredMatches.length > 0
            ? {
                wise_item_number: result.sourceProduct.wise_item_number,
                llm_matches: filteredMatches,
              }
            : null;
        })
        .filter(Boolean); // Remove null entries

      // Call bulk save API
      const response = await fetch(
        `${API_BASE_URL}/bulk-upload/save-cross-references`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ cross_references: saveData }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to save cross-references");
      }

      const result = await response.json();
      setSaveSuccess(true);
      console.log("Save result:", result);
    } catch (error) {
      console.error("Error saving cross-references:", error);
      setSaveError(error.message);
    } finally {
      setSaveLoading(false);
    }
  };

  return (
    <div className="h-full w-full bg-gradient-to-br from-gray-50 via-blue-50 to-gray-100 flex flex-col overflow-hidden">
      {/* Header */}
      <Header showScores={false} toggleScores={() => {}} />

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
        <div className="flex justify-between items-center">
          <div className="flex gap-0">
            <button
              onClick={() => navigate("/")}
              className="px-6 py-4 text-sm font-medium text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-colors"
            >
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
            <button className="px-5 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg">
              Bulk Upload
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-auto p-6">
        {/* Title */}
        <h1 className="text-2xl font-semibold text-gray-800 mb-6">
          Bulk Upload
        </h1>

        {/* Phase 1: File Upload */}
        {!showParsedData && (
          <div className="flex-1 flex items-start justify-center">
            <div className="w-full max-w-2xl">
              {/* Drag and Drop Area */}
              <div
                className={`border-2 border-dashed rounded-xl bg-white p-12 text-center transition-all cursor-pointer ${
                  isDragging
                    ? "border-blue-500 bg-blue-50"
                    : file
                    ? "border-green-400 bg-green-50"
                    : "border-gray-300 hover:border-blue-400 hover:bg-blue-50"
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileInput}
                  accept=".csv,.xlsx,.xls"
                  className="hidden"
                />
                <div className="flex flex-col items-center gap-4">
                  <div
                    className={`w-16 h-16 rounded-full flex items-center justify-center ${
                      file ? "bg-green-100" : "bg-blue-100"
                    }`}
                  >
                    {file ? (
                      <FiCheck className="w-8 h-8 text-green-600" />
                    ) : (
                      <FiUploadCloud className="w-8 h-8 text-blue-600" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                      {file
                        ? "File uploaded successfully!"
                        : "Drag and drop your files here"}
                    </h3>
                    <p className="text-sm text-gray-500 mb-4">
                      {file
                        ? file.name
                        : "or click to browse from your computer"}
                    </p>
                    <p className="text-xs text-gray-400">
                      Supported formats: CSV, XLSX, XLS
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      Required columns: {REQUIRED_HEADERS.join(", ")}
                    </p>
                  </div>
                  {!file && (
                    <button
                      className="mt-4 px-6 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        fileInputRef.current?.click();
                      }}
                    >
                      Browse Files
                    </button>
                  )}
                </div>
              </div>

              {/* Error Message */}
              {fileError && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                  <FiAlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                  <p className="text-sm text-red-700">{fileError}</p>
                </div>
              )}

              {/* File Preview Area */}
              <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-4">
                  Uploaded File
                </h4>
                {file ? (
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <FiFile className="w-8 h-8 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024).toFixed(2)} KB •{" "}
                          {parsedData.length} rows detected
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        clearFile();
                      }}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <FiX className="w-5 h-5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-8 text-gray-400">
                    <div className="flex flex-col items-center gap-2">
                      <FiFile className="w-8 h-8" />
                      <p className="text-sm">No files uploaded yet</p>
                    </div>
                  </div>
                )}

                {/* Proceed Button */}
                {file && parsedData.length > 0 && !fileError && (
                  <button
                    onClick={handleProceed}
                    className="mt-4 w-full px-6 py-3 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Proceed ({parsedData.length} products)
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Phase 2 & 3: Data Display and Cross-Reference */}
        {showParsedData && (
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {/* Action Buttons */}
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={() => {
                  setShowParsedData(false);
                  setCrossRefResults([]);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
              >
                ← Back to Upload
              </button>
              <div className="flex gap-3">
                {crossRefResults.length === 0 && (
                  <button
                    onClick={handleCrossReference}
                    disabled={crossRefLoading}
                    className="flex items-center gap-2 px-6 py-2.5 bg-purple-600 text-white text-sm font-semibold rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {crossRefLoading ? (
                      <>
                        <FiLoader className="w-4 h-4 animate-spin" />
                        {uploadStatus === "uploading" &&
                          "Uploading to inventory..."}
                        {uploadStatus === "uploaded" && "Indexing products..."}
                        {uploadStatus === "searching" &&
                          `Searching (${currentSearchIndex + 1}/${
                            parsedData.length
                          })`}
                      </>
                    ) : (
                      <>
                        <FiSearch className="w-4 h-4" />
                        Cross Reference
                      </>
                    )}
                  </button>
                )}
                {crossRefResults.length > 0 && !crossRefLoading && (
                  <button
                    onClick={handleSave}
                    disabled={saveLoading || saveSuccess}
                    className={`flex items-center gap-2 px-6 py-2.5 text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                      saveSuccess
                        ? "bg-green-600 text-white"
                        : "bg-green-600 text-white hover:bg-green-700"
                    }`}
                  >
                    {saveLoading ? (
                      <>
                        <FiLoader className="w-4 h-4 animate-spin" />
                        Saving...
                      </>
                    ) : saveSuccess ? (
                      <>
                        <FiCheck className="w-4 h-4" />
                        Saved Successfully
                      </>
                    ) : (
                      <>
                        <FiSave className="w-4 h-4" />
                        Save to Database
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Save Error/Success Messages */}
            {saveError && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                <FiAlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-sm text-red-700">{saveError}</p>
              </div>
            )}

            {saveSuccess && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
                <FiCheck className="w-5 h-5 text-green-500 flex-shrink-0" />
                <p className="text-sm text-green-700">
                  Cross-reference data saved successfully to database!
                </p>
              </div>
            )}

            {/* Cross-Reference Error */}
            {crossRefError && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                <FiAlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-sm text-red-700">{crossRefError}</p>
              </div>
            )}

            {/* Data Table */}
            <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-hidden flex flex-col">
              <div className="flex-1 overflow-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0 z-10 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        #
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Wise Item No
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Win Item Name
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Brand Name
                      </th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">
                        Catalog No
                      </th>
                      {crossRefResults.length > 0 && (
                        <th className="px-4 py-3 text-left font-semibold text-gray-700">
                          Similar Products
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {parsedData.map((row, index) => {
                      const crossRef = crossRefResults[index];
                      const isExpanded = expandedRows[index];

                      return (
                        <>
                          <tr
                            key={row.id}
                            className={`border-t border-gray-100 ${
                              crossRef?.error
                                ? "bg-red-50"
                                : crossRef?.notFoundMessage
                                ? "bg-orange-50"
                                : crossRef?.searchResults?.length > 0
                                ? "bg-green-50"
                                : ""
                            }`}
                          >
                            <td className="px-4 py-3 text-gray-600">
                              {index + 1}
                            </td>
                            <td className="px-4 py-3 font-medium text-gray-800">
                              {row.wise_item_number}
                            </td>
                            <td className="px-4 py-3 text-gray-700 max-w-xs truncate">
                              {row.win_item_name}
                            </td>
                            <td className="px-4 py-3 text-gray-600">
                              {row.brand_name}
                            </td>
                            <td className="px-4 py-3 text-gray-600">
                              {row.catalog_number}
                            </td>
                            {crossRefResults.length > 0 && (
                              <td className="px-4 py-3">
                                {crossRef ? (
                                  crossRef.error ? (
                                    <span className="text-red-500 text-xs">
                                      Error: {crossRef.error}
                                    </span>
                                  ) : crossRef.notFoundMessage ? (
                                    <span className="text-orange-500 text-xs">
                                      Not in inventory
                                    </span>
                                  ) : crossRef.searchResults?.length > 0 ? (
                                    <button
                                      onClick={() => toggleExpandRow(index)}
                                      className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs font-medium"
                                    >
                                      {(() => {
                                        const activeCount = getActiveMatchCount(
                                          index,
                                          crossRef.searchResults.length
                                        );
                                        const totalCount = crossRef.searchResults.length;
                                        return activeCount < totalCount
                                          ? `${activeCount} of ${totalCount} matches`
                                          : `${totalCount} matches`;
                                      })()}
                                      {isExpanded ? (
                                        <FiChevronUp className="w-4 h-4" />
                                      ) : (
                                        <FiChevronDown className="w-4 h-4" />
                                      )}
                                    </button>
                                  ) : (
                                    <span className="text-gray-400 text-xs">
                                      No matches
                                    </span>
                                  )
                                ) : crossRefLoading &&
                                  index === currentSearchIndex ? (
                                  <FiLoader className="w-4 h-4 animate-spin text-purple-500" />
                                ) : crossRefLoading &&
                                  index > currentSearchIndex ? (
                                  <span className="text-gray-400 text-xs">
                                    Pending...
                                  </span>
                                ) : null}
                              </td>
                            )}
                          </tr>
                          {/* Expanded Row - Similar Products */}
                          {isExpanded &&
                            crossRef?.searchResults?.length > 0 && (
                              <tr className="bg-blue-50">
                                <td colSpan={6} className="px-4 py-3">
                                  <div className="ml-8 overflow-x-auto max-w-full">
                                    <table className="w-full text-xs border border-blue-200 rounded">
                                      <thead className="bg-blue-100">
                                        <tr>
                                          <th className="px-3 py-2 text-left font-semibold text-blue-800">
                                            Rank
                                          </th>
                                          <th className="px-3 py-2 text-left font-semibold text-blue-800">
                                            Wise Item No
                                          </th>
                                          <th className="px-3 py-2 text-left font-semibold text-blue-800">
                                            Win Item Name
                                          </th>
                                          <th className="px-3 py-2 text-left font-semibold text-blue-800">
                                            Brand
                                          </th>
                                          <th className="px-3 py-2 text-left font-semibold text-blue-800">
                                            Score
                                          </th>
                                          <th className="px-3 py-2 text-left font-semibold text-blue-800">
                                            Varying Attrs
                                          </th>
                                          <th className="px-3 py-2 text-center font-semibold text-blue-800 w-12">
                                            Action
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {crossRef.searchResults.map(
                                          (match, matchIdx) => {
                                            const isExcluded =
                                              excludedMatches[index]?.has(matchIdx) || false;
                                            return (
                                              <tr
                                                key={matchIdx}
                                                className={`border-t border-blue-200 transition-opacity duration-200 ${
                                                  isExcluded ? "opacity-50" : ""
                                                }`}
                                              >
                                              <td className="px-3 py-2 text-blue-700">
                                                {match.rank || matchIdx + 1}
                                              </td>
                                              <td className="px-3 py-2 font-medium text-blue-800">
                                                {match.wise_item_number ||
                                                  match.document
                                                    ?.wise_item_number}
                                              </td>
                                              <td className="px-3 py-2 text-blue-700 max-w-xs truncate">
                                                {match.win_item_name ||
                                                  match.document?.win_item_name}
                                              </td>
                                              <td className="px-3 py-2 text-blue-600">
                                                {match.brand_name ||
                                                  match.document?.brand_name}
                                              </td>
                                              <td className="px-3 py-2">
                                                <span
                                                  className={`px-2 py-0.5 rounded text-white text-xs ${
                                                    (match.relevance_score ||
                                                      match.match_score /
                                                        100) >= 0.8
                                                      ? "bg-green-500"
                                                      : (match.relevance_score ||
                                                          match.match_score /
                                                            100) >= 0.6
                                                      ? "bg-yellow-500"
                                                      : "bg-orange-500"
                                                  }`}
                                                >
                                                  {match.relevance_score
                                                    ? (
                                                        match.relevance_score *
                                                        100
                                                      ).toFixed(1)
                                                    : match.match_score ||
                                                      "N/A"}
                                                  %
                                                </span>
                                              </td>
                                              <td className="px-3 py-2 text-blue-600">
                                                {match.varying_attributes
                                                  ?.length > 0
                                                  ? match.varying_attributes.join(
                                                      ", "
                                                    )
                                                  : "-"}
                                              </td>
                                              <td className="px-3 py-2 text-center">
                                                <button
                                                  onClick={() =>
                                                    handleRemoveMatch(index, matchIdx)
                                                  }
                                                  className="p-1 rounded hover:bg-blue-200 transition-colors"
                                                  title={
                                                    isExcluded
                                                      ? "Restore this match"
                                                      : "Remove this match"
                                                  }
                                                >
                                                  {isExcluded ? (
                                                    <FiRotateCcw className="w-4 h-4 text-green-600" />
                                                  ) : (
                                                    <FiX className="w-4 h-4 text-red-500 hover:text-red-700" />
                                                  )}
                                                </button>
                                              </td>
                                            </tr>
                                            );
                                          }
                                        )}
                                      </tbody>
                                    </table>
                                  </div>
                                </td>
                              </tr>
                            )}
                        </>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Summary */}
            <div className="mt-4 p-4 bg-white rounded-xl border border-gray-200 flex-shrink-0">
              <div className="flex items-center justify-between text-sm flex-wrap gap-4">
                <span className="text-gray-600">
                  Total Products: <strong>{parsedData.length}</strong>
                </span>
                {crossRefResults.length > 0 && (
                  <>
                    <span className="text-green-600">
                      With Matches:{" "}
                      <strong>
                        {
                          crossRefResults.filter(
                            (r) => r.searchResults?.length > 0
                          ).length
                        }
                      </strong>
                    </span>
                    {(() => {
                      const removedCount = getTotalRemovedCount();
                      return removedCount > 0 ? (
                        <span className="text-purple-600">
                          Removed Matches:{" "}
                          <strong>{removedCount}</strong>
                        </span>
                      ) : null;
                    })()}
                    <span className="text-orange-600">
                      Not in Inventory:{" "}
                      <strong>
                        {
                          crossRefResults.filter((r) => r.notFoundMessage)
                            .length
                        }
                      </strong>
                    </span>
                    <span className="text-red-600">
                      Errors:{" "}
                      <strong>
                        {crossRefResults.filter((r) => r.error).length}
                      </strong>
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default BulkUpload;
