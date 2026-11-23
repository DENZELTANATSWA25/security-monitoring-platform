
"""Benchmark RF behavioural history reconstruction with synthetic logins.

Run manually against security_test_db only. Not a pytest test.
All synthetic rows are rolled back after benchmarking.
"""

import asyncio
import os
import statistics
from datetime import datetime, timedelta
from time import perf_counter

from sqlalchemy import insert, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.login_attempt import LoginAttempt
from app.services.behavioural_detection.login_adapter import (
    extract_login_behaviour,
)

VOLUMES = (100, 1000, 5000)


async def benchmark_volume(session, volume):
    """Measure database retrieval and complete feature reconstruction."""

    now = datetime.utcnow().replace(microsecond=0)

    # Distribute synthetic authentication events across the past 24 hours.
    rows = [
        {
            "email": f"benchmark-{i % 100}@example.invalid",
            "successful": i % 5 != 0,
            "ip_address": f"192.0.2.{(i % 250) + 1}",
            "timestamp": now - timedelta(
                seconds=86300 - (i * 86000 / volume)
            ),
        }
        for i in range(volume)
    ]

    # Insert without committing. All records remain transaction-local.
    await session.execute(insert(LoginAttempt), rows)

    attempt = LoginAttempt(
        email="benchmark-target@example.invalid",
        successful=False,
        ip_address="203.0.113.10",
        timestamp=now,
    )

    session.add(attempt)
    await session.flush()

    cutoff = now - timedelta(hours=24)

    query = (
        select(LoginAttempt)
        .where(
            LoginAttempt.timestamp > cutoff,
            LoginAttempt.timestamp < now,
            LoginAttempt.id != attempt.id,
        )
        .order_by(
            LoginAttempt.timestamp,
            LoginAttempt.id,
        )
    )

    query_times = []
    extraction_times = []

    # Repeated measurements reduce single-run timing noise.
    for _ in range(3):
        start = perf_counter()
        result = await session.execute(query)
        history = result.scalars().all()
        query_times.append(perf_counter() - start)

        start = perf_counter()
        features = await extract_login_behaviour(
            session,
            attempt,
        )
        extraction_times.append(perf_counter() - start)

        assert len(features.as_vector()) == 22

    return {
        "volume": volume,
        "history_rows": len(history),
        "query_ms": round(
            statistics.median(query_times) * 1000, 2
        ),
        "full_extraction_ms": round(
            statistics.median(extraction_times) * 1000, 2
        ),
    }


async def main():
    source_url = make_url(os.environ["DATABASE_URL"])

    # Explicit safety gate: never benchmark against the application DB.
    if source_url.database != "security_test_db":
        raise SystemExit(
            "Benchmark requires DATABASE_URL=security_test_db."
        )

    engine = create_async_engine(
        source_url.render_as_string(hide_password=False)
    )

    try:
        async with engine.connect() as connection:
            revision = await connection.scalar(
                text("SELECT version_num FROM alembic_version")
            )

            if revision != "ae09bee04d97":
                raise SystemExit(
                    f"Unexpected database revision: {revision}"
                )

            await connection.rollback()

            session_factory = async_sessionmaker(
                bind=connection,
                expire_on_commit=False,
            )

            print("Synthetic behavioural history benchmark")
            print("Database: security_test_db")
            print()

            for volume in VOLUMES:
                transaction = await connection.begin()

                try:
                    async with session_factory() as session:
                        result = await benchmark_volume(
                            session,
                            volume,
                        )
                        print(result)
                finally:
                    await transaction.rollback()

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
