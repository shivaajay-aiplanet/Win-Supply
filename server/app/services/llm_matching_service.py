"""
LLM-based product matching service for intelligent product comparison.
Uses Azure OpenAI to match products based on critical and flexible attributes.
"""

import json
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from openai import AzureOpenAI
import psycopg2
from psycopg2.extras import RealDictCursor

from app.config.settings import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
    LLM_BATCH_SIZE,
    LLM_MAX_RESULTS,
    POSTGRES_CONNECTION_STRING,
    POSTGRES_TABLE_NAME,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System prompt for industrial product matching
SYSTEM_PROMPT = """You are an industrial/construction inventory expert. Your task is to find SIMILAR and ALTERNATIVE products that could substitute for the source product.

## YOUR GOAL
Find products that are FUNCTIONALLY SIMILAR to the source product. We want alternatives that could work as replacements. Do NOT only return exact matches - find ALL viable alternatives.

NOTE: You are only given wise_item_number and win_item_name (product description). Do NOT consider brand in your evaluation - focus only on technical specifications in the product name.

## PRODUCT CATEGORY RULES

### FANS (Duct Fans, Booster Fans, Exhaust Fans, Axial Fans)
**CRITICAL (Must Match):**
- Size/Diameter (e.g., 8 in. must match 8 in.) - This is the MOST important
- Product Type (Duct Fan, Booster Fan, Exhaust Fan - similar categories are acceptable)

**FLEXIBLE (Can Vary):**
- CFM: Can be EQUAL OR HIGHER (500 CFM is acceptable for 380 CFM request)
- Voltage: 110V, 115V, 120V are all interchangeable (standard US voltage)
- Additional features

### PIPES & FITTINGS
**CRITICAL (Must Match):**
- Diameter/Size (1/2 in., 3/4 in., etc.)
- Thread Type (NPT, BSP)
- Connection Type (threaded, flanged, welded)
- Material (when specified: copper, PVC, steel, brass)

**FLEXIBLE (Can Vary):**
- Pressure rating (if equal or higher)
- Length (if not critical)

### ELECTRICAL COMPONENTS
**CRITICAL (Must Match):**
- Voltage rating (120V vs 240V is NOT interchangeable)
- Amperage (must be equal or higher)
- Connector type

**FLEXIBLE (Can Vary):**
- Wattage (if higher), Color

### PUMPS
**CRITICAL (Must Match):**
- Voltage (115V/120V interchangeable, but 120V vs 240V is NOT)
- HP rating (should be equal or higher)
- Pump type (booster, centrifugal, etc.)

**FLEXIBLE (Can Vary):**
- GPM (if equal or higher)

## SCORING GUIDELINES
- 100: Exact same product (same wise_item_number or identical specs)
- 90-99: Same size/dimension, same type, minor spec differences (CFM higher, etc.)
- 80-89: Same size/dimension, same type, voltage compatible, CFM varies
- 70-79: Same size/dimension, similar type, multiple flexible attributes differ
- 60-69: Size matches but significant spec differences
- 50-59: Partial match, could work as alternative with limitations
- Below 50: Do not include (critical attribute mismatch like wrong size)

## IMPORTANT
- Return ALL products that score >= 50 (be generous, include more matches)
- Same SIZE with higher CFM should score 85-95
- The source product itself (if in list) should score 100
- Products with WRONG SIZE should score below 50 and be EXCLUDED
- Do NOT include "brand" in varying_attributes - we don't have brand info
- varying_attributes should only include: cfm, voltage, wattage, size, type, material, etc.

## OUTPUT FORMAT
Return ONLY a JSON array. Each item has key "r" with value in this exact format:
WISE_ITEM_NUMBER|SCORE|ATTRS

Where:
- WISE_ITEM_NUMBER: The product's wise_item_number
- SCORE: Integer 50-100 based on scoring guidelines above (MUST be a real score, NOT 0)
- ATTRS: Comma-separated varying attributes (or empty if none)

Use PIPE character | as delimiter (NOT dots).

Examples:
[
  {"r": "ACM09008|100|"},
  {"r": "SUPDB8|92|cfm"},
  {"r": "FCC46120002|85|cfm,voltage"},
  {"r": "AERAF08|78|cfm,type,voltage"}
]

CRITICAL RULES:
1. SCORE must be 50-100 based on actual evaluation, NEVER 0
2. Use | as delimiter
3. ATTRS can be empty but delimiter must be present
4. Return ONLY valid JSON array, no other text"""


def get_products_by_wise_item_numbers(
    wise_item_numbers: List[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch full product details from PostgreSQL for multiple wise_item_numbers.

    Returns:
        dict: Mapping of wise_item_number to full product data
    """
    if not wise_item_numbers:
        return {}

    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build query with IN clause
        placeholders = ",".join(["%s"] * len(wise_item_numbers))
        query = f"""
            SELECT id, wise_item_number, win_item_name, brand_name,
                   catalog_number, mainframe_description, preferred_supplier
            FROM public.{POSTGRES_TABLE_NAME}
            WHERE wise_item_number IN ({placeholders})
        """

        cursor.execute(query, tuple(wise_item_numbers))
        results = cursor.fetchall()

        # Create mapping
        products_map = {}
        for row in results:
            products_map[row["wise_item_number"]] = dict(row)

        logger.info(f"Fetched {len(products_map)} products from database")
        return products_map

    except Exception as e:
        logger.error(f"Error fetching products from database: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def get_cached_llm_matches(wise_item_number: str) -> List[Dict[str, Any]] | None:
    """
    Check cross_reference table for cached LLM matches.

    Args:
        wise_item_number: The source product's WISE item number

    Returns:
        List of cached matches in compact format, or None if not found
    """
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT llm_matches
            FROM public.cross_reference
            WHERE wise_item_number = %s
            """,
            (wise_item_number,),
        )

        result = cursor.fetchone()
        if result and result.get("llm_matches"):
            logger.info(f"✅ Cache HIT for {wise_item_number}")
            return result["llm_matches"]

        logger.info(f"❌ Cache MISS for {wise_item_number}")
        return None

    except Exception as e:
        logger.error(f"Error checking cross_reference cache: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_all_top_alternatives() -> Dict[str, Dict[str, Any]]:
    """
    Fetch all cross-reference entries and return a mapping of
    source_wise_item_number -> top alternative details (wise_item_number, match_score, varying_attributes).

    Returns:
        dict: Mapping of source wise_item_number to the best alternative's full data
    """
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT wise_item_number, llm_matches
            FROM public.cross_reference
            """
        )

        results = cursor.fetchall()
        alternatives_map = {}

        for row in results:
            source_wise_item = row.get("wise_item_number")
            llm_matches = row.get("llm_matches", [])

            if not llm_matches or not source_wise_item:
                continue

            # Parse compact format and collect all matches with scores and attrs
            # Format: {"r": "WISE_ITEM_NUMBER|SCORE|ATTRS"}
            matches_with_data = []

            for match in llm_matches:
                compact_str = match.get("r", "")
                if not compact_str:
                    continue

                parts = compact_str.split("|")
                if len(parts) >= 2:
                    match_wise_item = parts[0].strip()
                    try:
                        score = int(parts[1].strip())
                    except ValueError:
                        score = 0

                    # Parse varying attributes
                    varying_attrs = []
                    if len(parts) >= 3 and parts[2]:
                        varying_attrs = [
                            attr.strip() for attr in parts[2].split(",") if attr.strip()
                        ]

                    matches_with_data.append(
                        {
                            "wise_item_number": match_wise_item,
                            "match_score": score,
                            "varying_attributes": varying_attrs,
                        }
                    )

            # Sort by score descending
            matches_with_data.sort(key=lambda x: x["match_score"], reverse=True)

            # Find the best alternative that is NOT the same as the source
            for match_data in matches_with_data:
                if match_data["wise_item_number"] != source_wise_item:
                    alternatives_map[source_wise_item] = match_data
                    break

        logger.info(
            f"Fetched {len(alternatives_map)} top alternatives from cross_reference"
        )
        return alternatives_map

    except Exception as e:
        logger.error(f"Error fetching top alternatives: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def save_llm_matches_to_cache(
    wise_item_number: str, llm_matches: List[Dict[str, Any]]
) -> bool:
    """
    Save LLM matches to cross_reference table for future lookups.

    Args:
        wise_item_number: The source product's WISE item number
        llm_matches: List of matched products in compact format

    Returns:
        bool: True if saved successfully
    """
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor()

        # Use UPSERT (INSERT ON CONFLICT UPDATE) to handle duplicates
        cursor.execute(
            """
            INSERT INTO public.cross_reference (wise_item_number, llm_matches)
            VALUES (%s, %s)
            ON CONFLICT (wise_item_number)
            DO UPDATE SET llm_matches = EXCLUDED.llm_matches
            """,
            (wise_item_number, json.dumps(llm_matches)),
        )

        conn.commit()
        logger.info(
            f"✅ Saved {len(llm_matches)} matches to cache for {wise_item_number}"
        )
        return True

    except Exception as e:
        logger.error(f"Error saving to cross_reference cache: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def delete_match_from_cross_reference(
    source_wise_item_number: str, matched_wise_item_number: str
) -> Dict[str, Any]:
    """
    Delete a specific matched product from the cross_reference table.

    This removes a single match from the llm_matches JSONB array for a given
    source product. Used when a user reports an incorrect product match.

    Args:
        source_wise_item_number: The source product's WISE item number (the search query)
        matched_wise_item_number: The WISE item number of the match to delete

    Returns:
        dict: {"success": bool, "message": str, "remaining_matches": int}
    """
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # First, get the current llm_matches
        cursor.execute(
            """
            SELECT llm_matches
            FROM public.cross_reference
            WHERE wise_item_number = %s
            """,
            (source_wise_item_number,),
        )

        result = cursor.fetchone()
        if not result or not result.get("llm_matches"):
            return {
                "success": False,
                "message": f"No cross-reference found for {source_wise_item_number}",
                "remaining_matches": 0,
            }

        current_matches = result["llm_matches"]
        original_count = len(current_matches)

        # Filter out the match to delete
        # The format is {"r": "WISE_ITEM_NUMBER|SCORE|ATTRS"}
        updated_matches = [
            match
            for match in current_matches
            if not match.get("r", "").startswith(f"{matched_wise_item_number}|")
        ]

        new_count = len(updated_matches)

        if new_count == original_count:
            return {
                "success": False,
                "message": f"Match {matched_wise_item_number} not found in cross-reference for {source_wise_item_number}",
                "remaining_matches": original_count,
            }

        # Update the cross_reference table with the filtered matches
        cursor.execute(
            """
            UPDATE public.cross_reference
            SET llm_matches = %s, updated_at = CURRENT_TIMESTAMP
            WHERE wise_item_number = %s
            """,
            (json.dumps(updated_matches), source_wise_item_number),
        )

        conn.commit()
        logger.info(
            f"✅ Deleted match {matched_wise_item_number} from cross-reference for {source_wise_item_number}. "
            f"Remaining matches: {new_count}"
        )

        return {
            "success": True,
            "message": f"Successfully removed {matched_wise_item_number} from cross-reference",
            "remaining_matches": new_count,
        }

    except Exception as e:
        logger.error(f"Error deleting match from cross_reference: {e}")
        if conn:
            conn.rollback()
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "remaining_matches": 0,
        }
    finally:
        if conn:
            conn.close()


def parse_compact_llm_format(
    compact_matches: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Parse compact LLM format and convert to standard format.

    Args:
        compact_matches: List of {"r": "item|score|attrs", "l": likes, "d": dislikes} format (pipe delimiter)

    Returns:
        List of {"wise_item_number": ..., "match_score": ..., "varying_attributes": [...], "likes": int, "dislikes": int}
    """
    results = []
    for item in compact_matches:
        compact_str = item.get("r", "")
        if not compact_str:
            continue

        parts = compact_str.split("|")
        if len(parts) >= 2:
            wise_item_number = parts[0].strip()
            try:
                match_score = int(parts[1].strip())
            except ValueError:
                match_score = 50  # Default to minimum passing score

            varying_attrs = []
            if len(parts) >= 3 and parts[2]:
                varying_attrs = [
                    attr.strip() for attr in parts[2].split(",") if attr.strip()
                ]

            # Get like/dislike counts (default to 0)
            likes = item.get("l", 0)
            dislikes = item.get("d", 0)

            results.append(
                {
                    "wise_item_number": wise_item_number,
                    "match_score": match_score,
                    "varying_attributes": varying_attrs,
                    "likes": likes,
                    "dislikes": dislikes,
                }
            )

    return results


def get_azure_client() -> AzureOpenAI:
    """Create and return Azure OpenAI client."""
    return AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )


def build_user_prompt(
    query_text: str,
    source_product: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> str:
    """Build the user prompt with source product and candidates."""
    candidates_text = "\n".join(
        [
            f"- wise_item_number: {c.get('wise_item_number')}, win_item_name: {c.get('win_item_name')}"
            for c in candidates
        ]
    )

    return f"""## Source Product (What we're looking for matches for)
- Query Text: {query_text}
- WISE Item Number: {source_product.get('wise_item_number')}
- Product Name: {source_product.get('win_item_name')}

## Candidate Products to Evaluate
{candidates_text}

Evaluate each candidate against the source product. Return JSON array with match_score and varying_attributes for each."""


def process_batch(
    client: AzureOpenAI,
    query_text: str,
    source_product: Dict[str, Any],
    batch: List[Dict[str, Any]],
    batch_num: int,
) -> List[Dict[str, Any]]:
    """Process a single batch of candidates through the LLM."""
    try:
        logger.info(f"Processing batch {batch_num} with {len(batch)} candidates")

        user_prompt = build_user_prompt(query_text, source_product, batch)

        # Log the prompt being sent to LLM
        logger.info("=" * 60)
        logger.info(f"BATCH {batch_num} - PROMPT SENT TO LLM:")
        logger.info("=" * 60)
        logger.info(f"SYSTEM PROMPT:\n{SYSTEM_PROMPT[:500]}...")
        logger.info("-" * 60)
        logger.info(f"USER PROMPT:\n{user_prompt}")
        logger.info("=" * 60)

        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_completion_tokens=4096,
        )

        response_text = response.choices[0].message.content.strip()
        logger.info(f"Batch {batch_num} raw response: {response_text[:200]}...")

        # Parse JSON response
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        raw_results = json.loads(response_text)

        # Parse compact string format and convert to original dictionary format
        # Format: WISE_ITEM_NUMBER|SCORE|ATTRS (using pipe delimiter)
        results = []
        for item in raw_results:
            compact_str = item.get("r", "")
            if not compact_str:
                continue

            parts = compact_str.split("|")
            if len(parts) >= 2:
                wise_item_number = parts[0].strip()
                try:
                    match_score = int(parts[1].strip())
                except ValueError:
                    match_score = 50  # Default to minimum passing score

                # Parse varying attributes (may be empty)
                varying_attrs = []
                if len(parts) >= 3 and parts[2]:
                    varying_attrs = [
                        attr.strip() for attr in parts[2].split(",") if attr.strip()
                    ]

                results.append(
                    {
                        "wise_item_number": wise_item_number,
                        "match_score": match_score,
                        "varying_attributes": varying_attrs,
                    }
                )

        logger.info(f"Batch {batch_num} returned {len(results)} matched products")
        return results

    except json.JSONDecodeError as e:
        logger.error(f"Batch {batch_num} JSON parse error: {e}")
        return []
    except Exception as e:
        logger.error(f"Batch {batch_num} processing error: {e}")
        return []


def process_batches_parallel(
    query_text: str,
    source_product: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    max_workers: int = 4,
) -> List[Dict[str, Any]]:
    """Process multiple batches in parallel using ThreadPoolExecutor."""
    client = get_azure_client()

    # Split candidates into batches
    batches = [
        candidates[i : i + LLM_BATCH_SIZE]
        for i in range(0, len(candidates), LLM_BATCH_SIZE)
    ]

    logger.info(
        f"Split {len(candidates)} candidates into {len(batches)} batches of max {LLM_BATCH_SIZE}"
    )

    all_results = []

    if len(batches) == 1:
        # Single batch - process directly
        all_results = process_batch(client, query_text, source_product, batches[0], 1)
    else:
        # Multiple batches - process in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    process_batch, client, query_text, source_product, batch, i + 1
                )
                for i, batch in enumerate(batches)
            ]

            for future in futures:
                try:
                    batch_results = future.result(timeout=120)
                    all_results.extend(batch_results)
                except Exception as e:
                    logger.error(f"Batch future error: {e}")

    return all_results


def llm_match_products(
    query_text: str,
    source_product: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    top_k: int = None,
) -> Dict[str, Any]:
    """
    Main function to match products using LLM with cross-reference caching.

    Args:
        query_text: The search query text
        source_product: Source product details (wise_item_number, win_item_name)
        candidates: List of candidate documents from hybrid search
        top_k: Number of top results to return (default from settings)

    Returns:
        dict: Matched products sorted by match_score with metadata
    """
    if top_k is None:
        top_k = LLM_MAX_RESULTS

    source_wise_item = source_product.get("wise_item_number")

    logger.info("=" * 80)
    logger.info("LLM PRODUCT MATCHING")
    logger.info("=" * 80)
    logger.info(f"Source product: {source_wise_item}")
    logger.info(f"Query text: {query_text[:100]}...")

    # Step 1: Check cross-reference cache first
    logger.info("Checking cross-reference cache...")
    cached_matches = get_cached_llm_matches(source_wise_item)

    if cached_matches is not None:
        # Cache HIT - Parse cached results and return
        logger.info(f"🚀 Using cached results for {source_wise_item}")

        # Parse compact format to standard format
        parsed_results = parse_compact_llm_format(cached_matches)

        # Sort by match_score descending and take top_k
        parsed_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        top_results = parsed_results[:top_k]

        # Get wise_item_numbers for database lookup
        wise_item_numbers = [
            r.get("wise_item_number") for r in top_results if r.get("wise_item_number")
        ]

        # Fetch full product details from database
        logger.info(f"Fetching {len(wise_item_numbers)} products from database...")
        products_from_db = get_products_by_wise_item_numbers(wise_item_numbers)

        # Enrich with database data
        enriched_results = _enrich_results_with_db(top_results, products_from_db)

        logger.info(f"✅ Returning {len(enriched_results)} cached products")
        return {
            "matched_products": enriched_results,
            "total_matched": len(enriched_results),
            "from_cache": True,
            "processing_stats": {
                "total_candidates": 0,
                "batches_processed": 0,
                "cache_hit": True,
            },
        }

    # Cache MISS - Run full LLM pipeline
    logger.info(f"Running full LLM pipeline for {source_wise_item}...")
    logger.info(f"Total candidates: {len(candidates)}")

    if not candidates:
        logger.warning("No candidates provided for LLM matching")
        return {
            "matched_products": [],
            "total_matched": 0,
            "processing_stats": {
                "total_candidates": 0,
                "batches_processed": 0,
            },
        }

    try:
        # Process batches (parallel if needed)
        matched_results = process_batches_parallel(
            query_text, source_product, candidates
        )

        # Sort by match_score descending
        matched_results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

        # Save ALL results to cache (in compact format) before taking top_k
        # This allows future queries with different top_k to use the cache
        compact_matches = [
            {
                "r": f"{r.get('wise_item_number')}|{r.get('match_score', 0)}|{','.join(r.get('varying_attributes', []))}"
            }
            for r in matched_results
        ]
        save_llm_matches_to_cache(source_wise_item, compact_matches)

        # Take top_k results
        top_results = matched_results[:top_k]

        # Get wise_item_numbers from LLM results
        wise_item_numbers = [
            r.get("wise_item_number") for r in top_results if r.get("wise_item_number")
        ]

        # Fetch full product details from database
        logger.info(f"Fetching {len(wise_item_numbers)} products from database...")
        products_from_db = get_products_by_wise_item_numbers(wise_item_numbers)

        # Enrich results with full database data
        enriched_results = _enrich_results_with_db(top_results, products_from_db)

        logger.info(
            f"LLM matching complete. Returning {len(enriched_results)} products"
        )
        for idx, r in enumerate(enriched_results, 1):
            logger.info(
                f"  {idx}. {r.get('wise_item_number')} | {r.get('brand_name')} | Score: {r.get('match_score')} | Varying: {r.get('varying_attributes')}"
            )

        return {
            "matched_products": enriched_results,
            "total_matched": len(enriched_results),
            "from_cache": False,
            "processing_stats": {
                "total_candidates": len(candidates),
                "batches_processed": (len(candidates) + LLM_BATCH_SIZE - 1)
                // LLM_BATCH_SIZE,
                "results_before_top_k": len(matched_results),
                "cache_hit": False,
            },
        }

    except Exception as e:
        logger.error(f"LLM matching error: {e}", exc_info=True)
        return {
            "matched_products": [],
            "total_matched": 0,
            "error": str(e),
            "processing_stats": {
                "total_candidates": len(candidates),
                "batches_processed": 0,
            },
        }


def _enrich_results_with_db(
    results: List[Dict[str, Any]], products_from_db: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Helper function to enrich LLM results with database product details."""
    enriched_results = []
    for result in results:
        wise_num = result.get("wise_item_number")
        if wise_num in products_from_db:
            db_product = products_from_db[wise_num]
            enriched = {
                "id": db_product.get("id"),
                "wise_item_number": db_product.get("wise_item_number"),
                "win_item_name": db_product.get("win_item_name"),
                "brand_name": db_product.get("brand_name"),
                "catalog_number": db_product.get("catalog_number"),
                "mainframe_description": db_product.get("mainframe_description"),
                "preferred_supplier": db_product.get("preferred_supplier"),
                "match_score": result.get("match_score", 0),
                "varying_attributes": result.get("varying_attributes", []),
                "likes": result.get("likes", 0),
                "dislikes": result.get("dislikes", 0),
            }
            enriched_results.append(enriched)
        else:
            logger.warning(f"Product {wise_num} not found in database")
    return enriched_results


def update_match_feedback(
    source_wise_item_number: str,
    matched_wise_item_number: str,
    feedback_type: str,  # "like" or "dislike"
) -> Dict[str, Any]:
    """
    Update the like or dislike count for a specific match in the cross_reference table.
    If dislikes exceed 5, automatically removes the match.

    Args:
        source_wise_item_number: The source product's WISE item number
        matched_wise_item_number: The WISE item number of the match to update
        feedback_type: Either "like" or "dislike"

    Returns:
        dict: {"success": bool, "message": str, "likes": int, "dislikes": int, "removed": bool}
    """
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get the current llm_matches
        cursor.execute(
            """
            SELECT llm_matches
            FROM public.cross_reference
            WHERE wise_item_number = %s
            """,
            (source_wise_item_number,),
        )

        result = cursor.fetchone()
        if not result or not result.get("llm_matches"):
            return {
                "success": False,
                "message": f"No cross-reference found for {source_wise_item_number}",
                "likes": 0,
                "dislikes": 0,
                "removed": False,
            }

        current_matches = result["llm_matches"]
        updated_matches = []
        match_found = False
        likes = 0
        dislikes = 0
        removed = False

        for match in current_matches:
            compact_str = match.get("r", "")
            if compact_str.startswith(f"{matched_wise_item_number}|"):
                match_found = True
                # Get current counts (default to 0)
                likes = match.get("l", 0)
                dislikes = match.get("d", 0)

                # Update the count based on feedback type
                if feedback_type == "like":
                    likes += 1
                elif feedback_type == "dislike":
                    dislikes += 1

                # Check if dislikes exceed threshold
                if dislikes > 5:
                    removed = True
                    logger.info(
                        f"Auto-removing match {matched_wise_item_number} from {source_wise_item_number} "
                        f"due to {dislikes} dislikes"
                    )
                    # Don't add this match to updated_matches (effectively removing it)
                    continue

                # Update the match with new counts
                updated_match = {"r": compact_str, "l": likes, "d": dislikes}
                updated_matches.append(updated_match)
            else:
                updated_matches.append(match)

        if not match_found:
            return {
                "success": False,
                "message": f"Match {matched_wise_item_number} not found in cross-reference for {source_wise_item_number}",
                "likes": 0,
                "dislikes": 0,
                "removed": False,
            }

        # Update the cross_reference table
        cursor.execute(
            """
            UPDATE public.cross_reference
            SET llm_matches = %s, updated_at = CURRENT_TIMESTAMP
            WHERE wise_item_number = %s
            """,
            (json.dumps(updated_matches), source_wise_item_number),
        )

        conn.commit()
        logger.info(
            f"Updated feedback for {matched_wise_item_number} in {source_wise_item_number}: "
            f"likes={likes}, dislikes={dislikes}, removed={removed}"
        )

        return {
            "success": True,
            "message": (
                "Removed due to excessive dislikes"
                if removed
                else f"Successfully updated {feedback_type}"
            ),
            "likes": likes,
            "dislikes": dislikes,
            "removed": removed,
        }

    except Exception as e:
        logger.error(f"Error updating match feedback: {e}")
        if conn:
            conn.rollback()
        return {
            "success": False,
            "message": f"Database error: {str(e)}",
            "likes": 0,
            "dislikes": 0,
            "removed": False,
        }
    finally:
        if conn:
            conn.close()


def get_match_feedback(
    source_wise_item_number: str,
    matched_wise_item_number: str,
) -> Dict[str, Any]:
    """
    Get the current like and dislike counts for a specific match.

    Args:
        source_wise_item_number: The source product's WISE item number
        matched_wise_item_number: The WISE item number of the match

    Returns:
        dict: {"success": bool, "likes": int, "dislikes": int}
    """
    conn = None
    try:
        conn = psycopg2.connect(POSTGRES_CONNECTION_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT llm_matches
            FROM public.cross_reference
            WHERE wise_item_number = %s
            """,
            (source_wise_item_number,),
        )

        result = cursor.fetchone()
        if not result or not result.get("llm_matches"):
            return {"success": False, "likes": 0, "dislikes": 0}

        for match in result["llm_matches"]:
            compact_str = match.get("r", "")
            if compact_str.startswith(f"{matched_wise_item_number}|"):
                return {
                    "success": True,
                    "likes": match.get("l", 0),
                    "dislikes": match.get("d", 0),
                }

        return {"success": False, "likes": 0, "dislikes": 0}

    except Exception as e:
        logger.error(f"Error getting match feedback: {e}")
        return {"success": False, "likes": 0, "dislikes": 0}
    finally:
        if conn:
            conn.close()
