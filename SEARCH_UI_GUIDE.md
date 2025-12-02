# Search UI User Guide 🔍

## Quick Start Guide

### How to Search for Products

1. **Navigate to Inventory Page**
   - Open http://localhost:5174 in your browser
   - Click on "Inventory" in the navigation menu

2. **Enter Your Search Query**
   - Type a product name, description, brand, item number, or catalog number
   - Example: "4 x 12 x 6 in. 90-Degree Center End Register Boot"

3. **Configure Results (Optional)**
   - Select how many results you want to see: 10, 20, 50, or 100
   - Default is 20 results

4. **Execute Search**
   - Click the "Search" button, OR
   - Press Enter key

5. **View Results**
   - See products ranked by BM25 relevance score
   - Exact matches are highlighted in green
   - Each result shows a relevance score

6. **Return to Normal View**
   - Click "Reset" button to go back to paginated inventory

---

## UI Components Explained

### 1. Search Bar
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔍 [Search input field...                                    ] [▼20]│
│    [Search] [Reset]                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Components:**
- **Search Input**: Enter your query here
- **Top K Dropdown**: Select 10, 20, 50, or 100 results
- **Search Button**: Execute the search (or press Enter)
- **Reset Button**: Clear search and return to normal view

---

### 2. Search Results Summary
```
┌─────────────────────────────────────────────────────────────────────┐
│ 📊 Search Results                                                   │
│                                                                     │
│ Query: "register boot"                                              │
│ Total Matches: 10,000 | Returned: 20                                │
│ ✓ Exact Match Found                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Information Displayed:**
- **Query**: The search term you entered
- **Total Matches**: Total number of products matching your query
- **Returned**: Number of results shown (based on top_k)
- **Exact Match Indicator**: Shows if an exact match was found

---

### 3. Results Table

#### Normal Inventory View
```
┌──┬───────┬─────────────────┬────────┬─────────────┬──────────────┬─────────┐
│☐ │ Image │ Item Name       │ Brand  │ Item Number │ Model Number │ Actions │
├──┼───────┼─────────────────┼────────┼─────────────┼──────────────┼─────────┤
│☐ │  📦   │ Product Name    │ WATCO  │ 12345       │ ABC-123      │ ℹ️ <>   │
└──┴───────┴─────────────────┴────────┴─────────────┴──────────────┴─────────┘
```

#### Search Results View
```
┌──┬────────────┬───────┬─────────────────┬────────┬─────────────┬──────────────┬─────────────┬─────────┐
│☐ │ BM25 Score │ Image │ Item Name       │ Brand  │ Item Number │ Catalog Num  │ Description │ Actions │
├──┼────────────┼───────┼─────────────────┼────────┼─────────────┼──────────────┼─────────────┼─────────┤
│☐ │   25.04    │  📦   │ Product Name    │ WATCO  │ 12345       │ CAT-456      │ Full desc   │ ℹ️ <>   │
│  │ ✓ Exact    │       │                 │        │             │              │             │         │
│  │   Match    │       │                 │        │             │              │             │         │
├──┼────────────┼───────┼─────────────────┼────────┼─────────────┼──────────────┼─────────────┼─────────┤
│☐ │   24.81    │  📦   │ Similar Product │ BRAND  │ 67890       │ CAT-789      │ Description │ ℹ️ <>   │
└──┴────────────┴───────┴─────────────────┴────────┴─────────────┴──────────────┴─────────────┴─────────┘
```

**Additional Columns in Search Mode:**
- **BM25 Score**: Relevance score (higher = more relevant)
- **Description**: Full product description
- **Exact Match Indicator**: Green checkmark for exact matches

**Visual Indicators:**
- **Exact Match Row**: Green background with green left border
- **Score Badge**: Blue background with white text
- **Exact Match Label**: Green text with checkmark

---

### 4. Footer

#### Normal View
```
┌─────────────────────────────────────────────────────────────────────┐
│ 0 items selected | 115,668 results found                            │
│                                          [← Previous] Page 1 of 5784 [Next →] │
└─────────────────────────────────────────────────────────────────────┘
```

#### Search View
```
┌─────────────────────────────────────────────────────────────────────┐
│ 20 results shown | 10,000 total matches                             │
└─────────────────────────────────────────────────────────────────────┘
```

**Note**: Pagination is hidden in search mode since results are already limited by top_k.

---

## Visual Indicators Guide

### BM25 Score Badge
```
┌──────────┐
│  25.04   │  ← Blue background, white text, bold font
└──────────┘
```
- **High Score (>20)**: Likely an exact or very close match
- **Medium Score (10-20)**: Good relevance
- **Low Score (<10)**: Partial match

### Exact Match Indicator
```
┌──────────────┐
│    25.04     │
│ ✓ Exact Match│  ← Green text with checkmark
└──────────────┘
```
- Appears below the score badge
- Only shown for exact matches
- Green color for easy identification

### Exact Match Row Highlighting
```
┌─│─────────────────────────────────────────────────────────────────┐
│ │ ☐ │ 25.04 │ 📦 │ Product Name │ ...                            │  ← Green left border
│ │   │ ✓ Exact│    │              │                                │  ← Green background
└─│─────────────────────────────────────────────────────────────────┘
  └─ Green accent border (4px wide)
```

---

## Search Tips

### 1. **Exact Product Name**
- Enter the full product name for best results
- Example: "4 x 12 x 6 in. 90-Degree Center End Register Boot"
- Expected: Exact match with high score (~25)

### 2. **Partial Product Name**
- Enter key words from the product name
- Example: "register boot"
- Expected: Multiple related products ranked by relevance

### 3. **Brand Search**
- Search by brand name to find all products from that brand
- Example: "WATCO"
- Expected: All WATCO brand products

### 4. **Item Number Search**
- Search by item number or catalog number
- Example: "12345"
- Expected: Products with matching item/catalog numbers

### 5. **Description Search**
- Search by product description or features
- Example: "90-degree center end"
- Expected: Products with matching descriptions

### 6. **Combination Search**
- Combine multiple search terms
- Example: "WATCO register boot"
- Expected: WATCO brand register boots

---

## Understanding BM25 Scores

### What is BM25?
BM25 (Best Matching 25) is a ranking function used to estimate the relevance of documents to a search query. Higher scores indicate better matches.

### Score Ranges
- **25+**: Exact or near-exact match
- **20-25**: Very high relevance
- **15-20**: High relevance
- **10-15**: Good relevance
- **5-10**: Moderate relevance
- **<5**: Low relevance

### Factors Affecting Score
1. **Term Frequency**: How often search terms appear in the product
2. **Document Length**: Shorter documents with matches score higher
3. **Field Boosting**: Matches in important fields (name, brand) score higher
4. **Inverse Document Frequency**: Rare terms score higher than common terms

---

## Common Use Cases

### Use Case 1: Find Exact Product
**Goal**: Find a specific product by name

**Steps**:
1. Enter the full product name
2. Set top_k to 10 (fewer results)
3. Click Search
4. Look for the green highlighted row (exact match)

**Example**: "4 x 12 x 6 in. 90-Degree Center End Register Boot"

---

### Use Case 2: Find Similar Products
**Goal**: Find products similar to a known product

**Steps**:
1. Enter key features or partial name
2. Set top_k to 50 (more results)
3. Click Search
4. Review results sorted by relevance score

**Example**: "register boot 90-degree"

---

### Use Case 3: Browse by Brand
**Goal**: See all products from a specific brand

**Steps**:
1. Enter the brand name
2. Set top_k to 100 (maximum results)
3. Click Search
4. Review all brand products

**Example**: "WATCO"

---

### Use Case 4: Find by Item Number
**Goal**: Locate a product using its item or catalog number

**Steps**:
1. Enter the item number or catalog number
2. Set top_k to 10
3. Click Search
4. Find the exact match

**Example**: "WIS-12345"

---

## Keyboard Shortcuts

- **Enter**: Execute search (when in search input field)
- **Tab**: Navigate between search input and top_k dropdown
- **Escape**: (Future) Clear search and reset

---

## Troubleshooting

### No Results Found
**Problem**: Search returns 0 results

**Solutions**:
- Check spelling of search terms
- Try fewer or more general search terms
- Remove special characters
- Try searching by brand or category instead

---

### Too Many Results
**Problem**: Search returns thousands of results

**Solutions**:
- Add more specific search terms
- Include brand name or model number
- Use exact product name if known
- Reduce top_k to see only top matches

---

### Exact Match Not Highlighted
**Problem**: Expected exact match but no green highlighting

**Explanation**:
- Exact match detection uses score threshold (>20) or text matching
- If score is below 20, it won't be highlighted even if it seems exact
- Try entering the full product name for better matching

---

### Slow Search Performance
**Problem**: Search takes a long time

**Solutions**:
- Reduce top_k to 10 or 20
- Use more specific search terms
- Check internet connection
- Ensure backend API is running

---

## API Information

### Search Endpoint
```
GET http://localhost:8000/api/search?q={query}&top_k={number}
```

### Parameters
- **q** (required): Search query string
- **top_k** (optional): Number of results to return (default: 20)

### Response Format
```json
{
  "query": "register boot",
  "total_hits": 10000,
  "returned_count": 20,
  "results": [
    {
      "id": 62,
      "score": 25.04,
      "document": {
        "win_item_name": "Product Name",
        "brand_name": "WATCO",
        "wise_item_number": "12345",
        "catalog_number": "CAT-456",
        "mainframe_description": "Full description"
      }
    }
  ]
}
```

---

## Support

### Need Help?
- Check the API documentation: http://localhost:8000/docs
- Review the implementation guide: FRONTEND_SEARCH_INTEGRATION.md
- Check the backend logs for errors

### Reporting Issues
When reporting issues, please include:
1. Search query used
2. Expected results
3. Actual results
4. Screenshots (if applicable)
5. Browser console errors (if any)

---

## Summary

The search interface provides a powerful, user-friendly way to find products using BM25 keyword search. Key features include:

✅ Natural language search
✅ Relevance scoring
✅ Exact match highlighting
✅ Configurable result count
✅ Clean, professional UI
✅ Fast search performance

**Happy Searching! 🎉**

