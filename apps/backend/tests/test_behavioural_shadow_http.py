
"""HTTP-level regression tests for behavioural RF shadow inference."""

from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alert import Alert
from app.models.login_attempt import LoginAttempt
from app.models.user import User
from app.services.behavioural_detection.inference import (
    BehaviouralDetectionResult,
    detect_behavioural_anomaly,
)


LOGIN_URL = "/api/v1/auth/login"
VALID_PASSWORD = "TestPassword123!"
INVALID_PASSWORD = "DefinitelyWrongPassword!"


def credentials(email: str, password: str) -> dict[str, str]:
    """Build an HTTP login payload."""
    return {"email": email, "password": password}


async def count_attempts(
    db: AsyncSession,
    email: str,
) -> int:
    """Count recorded attempts for the test account."""
    result = await db.execute(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.email == email,
        )
    )
    return result.scalar_one()


async def count_rf_alerts(db: AsyncSession) -> int:
    """Count RF-specific alerts, which shadow mode must never create."""
    result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.alert_type == "BEHAVIOURAL_RF_ANOMALY",
        )
    )
    return result.scalar_one()


async def test_successful_http_login_shadow_disabled(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Shadow OFF must not invoke behavioural inference."""

    monkeypatch.setattr(settings, "BEHAVIOURAL_RF_SHADOW_ENABLED", False)

    with patch(
        "app.services.login_attempt_service.detect_behavioural_anomaly",
    ) as prediction:
        response = await client.post(
            LOGIN_URL,
            json=credentials(viewer_user.email, VALID_PASSWORD),
        )

    assert response.status_code == 200
    assert response.json()["access_token"]
    prediction.assert_not_called()
    assert await count_attempts(db_session, viewer_user.email) == 1


async def test_successful_http_login_runs_real_rf(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Shadow ON must execute real RF inference without affecting login."""

    monkeypatch.setattr(settings, "BEHAVIOURAL_RF_SHADOW_ENABLED", True)
    results = []

    def capture_prediction(features):
        result = detect_behavioural_anomaly(features)
        results.append(result)
        return result

    with patch(
        "app.services.login_attempt_service.detect_behavioural_anomaly",
        side_effect=capture_prediction,
    ) as prediction:
        response = await client.post(
            LOGIN_URL,
            json=credentials(viewer_user.email, VALID_PASSWORD),
        )

    assert response.status_code == 200
    assert response.json()["access_token"]
    prediction.assert_called_once()

    assert len(results) == 1
    assert results[0].available is True
    assert results[0].score is not None
    assert 0.0 <= results[0].score <= 1.0
    assert results[0].model_version == "behavioural_random_forest_v3"

    assert await count_attempts(db_session, viewer_user.email) == 1
    assert await count_rf_alerts(db_session) == 0


async def test_failed_http_login_runs_shadow_without_authentication(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Invalid credentials remain rejected even when RF inference runs."""

    monkeypatch.setattr(settings, "BEHAVIOURAL_RF_SHADOW_ENABLED", True)

    with patch(
        "app.services.login_attempt_service.detect_behavioural_anomaly",
        wraps=detect_behavioural_anomaly,
    ) as prediction:
        response = await client.post(
            LOGIN_URL,
            json=credentials(viewer_user.email, INVALID_PASSWORD),
        )

    assert response.status_code == 401
    prediction.assert_called_once()
    assert await count_attempts(db_session, viewer_user.email) == 1
    assert await count_rf_alerts(db_session) == 0


async def test_repeated_http_logins_use_prior_history(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Repeated logins must produce vectors using prior login history."""

    monkeypatch.setattr(settings, "BEHAVIOURAL_RF_SHADOW_ENABLED", True)
    vectors = []

    def capture_prediction(features):
        vectors.append(features)
        return detect_behavioural_anomaly(features)

    with patch(
        "app.services.login_attempt_service.detect_behavioural_anomaly",
        side_effect=capture_prediction,
    ):
        for password in [
            INVALID_PASSWORD,
            INVALID_PASSWORD,
            VALID_PASSWORD,
        ]:
            response = await client.post(
                LOGIN_URL,
                json=credentials(viewer_user.email, password),
            )
            assert response.status_code == (
                200 if password == VALID_PASSWORD else 401
            )

    assert len(vectors) == 3
    assert all(len(vector.as_vector()) == 22 for vector in vectors)

    # The first event has no earlier account history.
    first = vectors[0].as_dict()
    assert first["account_events_1h"] == 0.0
    assert first["account_failures_1h"] == 0.0
    assert first["account_history_available"] == 0.0

    # Subsequent events can use strictly earlier attempts.
    # These values assume distinct timestamps for the HTTP requests.
    second = vectors[1].as_dict()
    third = vectors[2].as_dict()

    assert second["account_events_1h"] == 1.0
    assert second["account_failures_1h"] == 1.0

    assert third["account_events_1h"] == 2.0
    assert third["account_failures_1h"] == 2.0
    assert await count_attempts(db_session, viewer_user.email) == 3
    assert await count_rf_alerts(db_session) == 0


async def test_unavailable_rf_does_not_interrupt_http_login(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Unavailable inference must not block valid authentication."""

    monkeypatch.setattr(settings, "BEHAVIOURAL_RF_SHADOW_ENABLED", True)

    unavailable = BehaviouralDetectionResult(
        available=False,
        is_anomaly=False,
        score=None,
        model_version="behavioural_random_forest_v3",
        reason="Behavioural model unavailable.",
    )

    with patch(
        "app.services.login_attempt_service.detect_behavioural_anomaly",
        return_value=unavailable,
    ) as prediction:
        response = await client.post(
            LOGIN_URL,
            json=credentials(viewer_user.email, VALID_PASSWORD),
        )

    assert response.status_code == 200
    prediction.assert_called_once()
    assert await count_attempts(db_session, viewer_user.email) == 1
    assert await count_rf_alerts(db_session) == 0


async def test_missing_model_preserves_http_authentication(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
    tmp_path,
) -> None:
    """A genuinely missing model must not interrupt authentication."""

    monkeypatch.setattr(settings, "BEHAVIOURAL_RF_SHADOW_ENABLED", True)

    missing_path = tmp_path / "missing-model.joblib"
    results = []

    def predict_with_missing_model(features):
        result = detect_behavioural_anomaly(
            features,
            model_path=missing_path,
        )
        results.append(result)
        return result

    with patch(
        "app.services.login_attempt_service.detect_behavioural_anomaly",
        side_effect=predict_with_missing_model,
    ) as prediction:
        response = await client.post(
            LOGIN_URL,
            json=credentials(viewer_user.email, VALID_PASSWORD),
        )

    assert response.status_code == 200
    prediction.assert_called_once()
    assert len(results) == 1
    assert results[0].available is False
    assert results[0].score is None
    assert results[0].reason == "Behavioural model unavailable."

    assert await count_attempts(db_session, viewer_user.email) == 1
    assert await count_rf_alerts(db_session) == 0


async def test_corrupted_model_preserves_http_authentication(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
    tmp_path,
) -> None:
    """An invalid model checksum must not interrupt authentication."""

    monkeypatch.setattr(settings, "BEHAVIOURAL_RF_SHADOW_ENABLED", True)

    corrupted_path = tmp_path / "corrupted-model.joblib"
    corrupted_path.write_bytes(b"invalid frozen model artifact")

    results = []

    def predict_with_corrupted_model(features):
        result = detect_behavioural_anomaly(
            features,
            model_path=corrupted_path,
        )
        results.append(result)
        return result

    with patch(
        "app.services.login_attempt_service.detect_behavioural_anomaly",
        side_effect=predict_with_corrupted_model,
    ):
        response = await client.post(
            LOGIN_URL,
            json=credentials(viewer_user.email, VALID_PASSWORD),
        )

    assert response.status_code == 200
    assert len(results) == 1
    assert results[0].available is False
    assert results[0].score is None
    assert results[0].reason == "Behavioural model unavailable."

    assert await count_attempts(db_session, viewer_user.email) == 1
    assert await count_rf_alerts(db_session) == 0


async def test_invalid_behavioural_features_do_not_block_login(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Invalid ML feature data must not interrupt authentication."""

    from app.services.behavioural_detection.login_adapter import (
        BehaviouralFeatureError,
    )

    monkeypatch.setattr(settings, "BEHAVIOURAL_RF_SHADOW_ENABLED", True)

    with (
        patch(
            "app.services.login_attempt_service.extract_login_behaviour",
            side_effect=BehaviouralFeatureError("Invalid synthetic data"),
        ) as extraction,
        patch(
            "app.services.login_attempt_service.detect_behavioural_anomaly",
        ) as prediction,
    ):
        response = await client.post(
            LOGIN_URL,
            json=credentials(viewer_user.email, VALID_PASSWORD),
        )

    assert response.status_code == 200
    extraction.assert_awaited_once()
    prediction.assert_not_called()

    assert await count_attempts(db_session, viewer_user.email) == 1
    assert await count_rf_alerts(db_session) == 0



async def test_shadow_history_database_failure_rolls_back_login_attempt(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Database failures must propagate and roll back the login attempt."""

    monkeypatch.setattr(
        settings,
        "BEHAVIOURAL_RF_SHADOW_ENABLED",
        True,
    )

    # Save scalar values before rollback expires ORM attributes.
    email = viewer_user.email

    with patch(
        "app.services.login_attempt_service.extract_login_behaviour",
        side_effect=RuntimeError("Synthetic database failure"),
    ):
        try:
            await client.post(
                LOGIN_URL,
                json=credentials(email, VALID_PASSWORD),
            )
        except RuntimeError as exc:
            assert str(exc) == "Synthetic database failure"
        else:
            raise AssertionError(
                "Expected database failure to propagate."
            )

    # Query using the saved string, not an expired ORM attribute.
    assert await count_attempts(db_session, email) == 0

