"""Asynchronous execution strategies for behavioural RF inference."""

import asyncio

from app.services.behavioural_detection.inference import (
    detect_behavioural_anomaly,
)

# Bound concurrent offloaded predictions to one per process.
_RF_SEMAPHORE = asyncio.Semaphore(1)


async def run_behavioural_inference(
    features,
    *,
    strategy: str = "direct",
):
    """Execute frozen RF inference using the selected strategy."""

    if strategy == "direct":
        # Existing synchronous execution.
        return detect_behavioural_anomaly(features)

    if strategy == "threaded":
        # Run inference in a worker thread.
        return await asyncio.to_thread(
            detect_behavioural_anomaly,
            features,
        )

    if strategy == "bounded":
        # Prevent multiple simultaneous offloaded RF predictions.
        async with _RF_SEMAPHORE:
            return await asyncio.to_thread(
                detect_behavioural_anomaly,
                features,
            )

    raise ValueError(
        f"Unsupported RF inference strategy: {strategy}"
    )
