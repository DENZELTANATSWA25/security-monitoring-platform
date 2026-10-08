"""Offline command for training the ML anomaly-detection model."""

import argparse
import asyncio
from pathlib import Path

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.anomaly_detection.training_service import (
    train_from_historical_events,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Train the Isolation Forest anomaly-detection model "
            "from historical security events."
        )
    )

    parser.add_argument(
        "--version",
        required=True,
        help="Version identifier for the trained model.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10_000,
        help="Maximum number of historical events used for training.",
    )

    return parser.parse_args()


async def train(
    *,
    version: str,
    limit: int,
) -> None:
    """Run the database-backed anomaly-model training workflow."""

    model_directory = Path(
        settings.ANOMALY_MODEL_DIRECTORY
    )

    async with AsyncSessionLocal() as db:
        event_count = await train_from_historical_events(
            db,
            model_directory=model_directory,
            version=version,
            limit=limit,
        )

    print(
        f"Anomaly model {version!r} trained successfully "
        f"using {event_count} historical events."
    )
    print(
        f"Model artifacts saved to: {model_directory}"
    )


def main() -> None:
    """Execute the offline training command."""

    args = parse_args()

    asyncio.run(
        train(
            version=args.version,
            limit=args.limit,
        )
    )


if __name__ == "__main__":
    main()