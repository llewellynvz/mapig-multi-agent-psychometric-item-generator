"""Correlation estimation agent using GPT-5.2.

Implements CORR-01 and CORR-03 requirements.
"""

import asyncio
import json
import logging
from typing import List

from backend.agents.llm_factory import get_gpt52_analytics_model
from backend.schemas import CorrelationCell

logger = logging.getLogger("lmaig")


async def estimate_pairwise_correlations(
    items: List[str],
    construct_name: str,
    batch_size: int = 20
) -> List[CorrelationCell]:
    """Estimate pairwise correlations using GPT-5.2 with batching.

    Args:
        items: List of item texts
        construct_name: Name of the construct for psychometric context
        batch_size: Number of pairs per LLM batch (default 20)

    Returns:
        List of CorrelationCell objects with correlation + 95% CI for each pair
    """
    num_items = len(items)

    # Generate all unique pairs (upper-triangular)
    pairs = []
    for i in range(num_items):
        for j in range(i + 1, num_items):
            pairs.append((i, j))

    logger.info(f"Estimating {len(pairs)} pairwise correlations for {num_items} items in batches of {batch_size}")

    # Batch pairs
    batches = []
    for batch_start in range(0, len(pairs), batch_size):
        batch_pairs = pairs[batch_start:batch_start + batch_size]
        batches.append(batch_pairs)

    logger.info(f"Created {len(batches)} batches")

    # Get GPT-5.2 model
    model = get_gpt52_analytics_model()

    # Process batches in parallel (max 5 concurrent to avoid rate limits)
    semaphore = asyncio.Semaphore(5)

    async def process_batch(batch_pairs: List[tuple], batch_idx: int) -> List[CorrelationCell]:
        """Process a single batch of pairs."""
        async with semaphore:
            # Build prompt
            pairs_text = "\n".join([
                f"{i+1}. Item {i_idx}: \"{items[i_idx]}\"\n   Item {j_idx}: \"{items[j_idx]}\""
                for i, (i_idx, j_idx) in enumerate(batch_pairs)
            ])

            prompt = f"""You are a psychometric expert estimating inter-item correlations for a scale measuring "{construct_name}".

For each pair of items below, estimate:
1. The expected correlation coefficient (Pearson r, range -1.0 to 1.0)
2. A 95% confidence interval (ci_low, ci_high)

Consider:
- How strongly each item measures the same underlying construct
- Semantic similarity and conceptual overlap
- Typical psychometric properties of well-designed scales

Item pairs to analyze:
{pairs_text}

Respond with ONLY a JSON array of objects. Each object must have:
- "item_i_index": first item index (0-based)
- "item_j_index": second item index (0-based)
- "correlation": estimated correlation (-1.0 to 1.0)
- "ci_low": lower bound of 95% CI
- "ci_high": upper bound of 95% CI

Example format:
[
  {{"item_i_index": 0, "item_j_index": 1, "correlation": 0.75, "ci_low": 0.65, "ci_high": 0.85}},
  {{"item_i_index": 0, "item_j_index": 2, "correlation": 0.68, "ci_low": 0.58, "ci_high": 0.78}}
]

Respond with ONLY the JSON array, no other text."""

            # Call LLM with retry logic
            max_retries = 1
            for attempt in range(max_retries + 1):
                try:
                    response = await model.ainvoke([{"role": "user", "content": prompt}])
                    content = response.content.strip()

                    # Parse JSON
                    parsed = json.loads(content)

                    # Convert to CorrelationCell objects
                    cells = []
                    for item in parsed:
                        cell = CorrelationCell(
                            item_i_index=item["item_i_index"],
                            item_j_index=item["item_j_index"],
                            correlation=item["correlation"],
                            ci_low=item["ci_low"],
                            ci_high=item["ci_high"]
                        )
                        cells.append(cell)

                    logger.info(f"Batch {batch_idx + 1}: Successfully parsed {len(cells)} correlation cells")
                    return cells

                except json.JSONDecodeError as e:
                    if attempt < max_retries:
                        logger.warning(f"Batch {batch_idx + 1}: JSON parse error on attempt {attempt + 1}, retrying: {e}")
                        continue
                    else:
                        logger.error(f"Batch {batch_idx + 1}: JSON parse error after {max_retries + 1} attempts, skipping batch: {e}")
                        return []

                except Exception as e:
                    logger.error(f"Batch {batch_idx + 1}: Unexpected error: {e}")
                    return []

            return []

    # Process all batches in parallel
    tasks = [process_batch(batch_pairs, i) for i, batch_pairs in enumerate(batches)]
    batch_results = await asyncio.gather(*tasks)

    # Flatten results
    all_cells = []
    for batch_cells in batch_results:
        all_cells.extend(batch_cells)

    logger.info(f"Correlation estimation complete: {len(all_cells)} / {len(pairs)} pairs estimated")

    return all_cells
