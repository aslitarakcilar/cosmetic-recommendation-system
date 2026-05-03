from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.interaction_model import Interaction
from app.main import app
from app.recommendation_event_model import RecommendationEvent, RecommendationEventItem
from app.schemas.recommendation import RecommendationItem
from app.user_model import User


class ApiFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.db"
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        Base.metadata.create_all(bind=self.engine)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.tempdir.cleanup()

    def register_user(self, email: str = "test@example.com", password: str = "secret12") -> dict:
        response = self.client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "skin_type": "dry",
                "skin_tone": "light",
                "undertone": "warm",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def login_headers(self, email: str = "test@example.com", password: str = "secret12") -> dict[str, str]:
        response = self.client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 200)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def admin_headers(self) -> dict[str, str]:
        self.register_user(email="aslinur0506@gmail.com")
        return self.login_headers(email="aslinur0506@gmail.com")

    def test_register_duplicate_and_login_flow(self) -> None:
        created = self.register_user()
        self.assertEqual(created["email"], "test@example.com")
        self.assertEqual(created["skin_type"], "dry")

        duplicate = self.client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "secret12",
                "skin_type": "dry",
                "skin_tone": "light",
                "undertone": "warm",
            },
        )
        self.assertEqual(duplicate.status_code, 409)

        ok_login = self.client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "secret12"},
        )
        self.assertEqual(ok_login.status_code, 200)
        self.assertIn("access_token", ok_login.json())

        bad_login = self.client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrong-pass"},
        )
        self.assertEqual(bad_login.status_code, 401)

    def test_rate_upserts_single_interaction_record(self) -> None:
        self.register_user()
        headers = self.login_headers()

        first = self.client.post(
            "/interactions/rate",
            json={"product_id": "p-123", "rating": 5},
            headers=headers,
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["rating"], 5)

        second = self.client.post(
            "/interactions/rate",
            json={"product_id": "p-123", "rating": 3},
            headers=headers,
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["rating"], 3)

        listed = self.client.get("/interactions/mine", headers=headers)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()), 1)
        self.assertEqual(listed.json()[0]["rating"], 3)

        with self.SessionLocal() as db:
            count = (
                db.query(func.count(Interaction.id))
                .filter(Interaction.product_id == "p-123")
                .scalar()
            )
        self.assertEqual(count, 1)

    def test_profile_read_and_update_flow(self) -> None:
        self.register_user()
        headers = self.login_headers()

        me = self.client.get("/users/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["skin_tone"], "light")

        updated = self.client.patch(
            "/users/me",
            json={"skin_type": "oily", "skin_tone": "medium", "undertone": "neutral"},
            headers=headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["skin_type"], "oily")
        self.assertEqual(updated.json()["undertone"], "neutral")

        with self.SessionLocal() as db:
            user = db.query(User).filter(User.email == "test@example.com").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.skin_type, "oily")
            self.assertEqual(user.skin_tone, "medium")

    def test_recommendations_auth_and_response_shape(self) -> None:
        unauthorized = self.client.post(
            "/recommendations",
            json={"category": "Body Sunscreen", "top_n": 5},
        )
        self.assertEqual(unauthorized.status_code, 401)

        self.register_user()
        headers = self.login_headers()

        fake_items = [
            RecommendationItem(
                product_id="p1",
                product_name="Sample Product",
                brand_name="Sample Brand",
                primary_category="Skincare",
                secondary_category="Sunscreen",
                tertiary_category="Body Sunscreen",
                price_usd=19.0,
                rating=4.6,
                score=0.9,
            )
        ]

        with patch(
            "app.routers.recommendations.get_recommendations",
            return_value=("lightfm", "Test aciklamasi", fake_items),
        ):
            response = self.client.post(
                "/recommendations",
                json={"category": "Body Sunscreen", "top_n": 5},
                headers=headers,
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["model_used"], "lightfm")
        self.assertEqual(body["model_explanation"], "Test aciklamasi")
        self.assertEqual(body["total_recommendations"], 1)
        self.assertGreater(body["recommendation_event_id"], 0)
        self.assertEqual(len(body["recommendations"]), 1)
        self.assertEqual(body["recommendations"][0]["product_id"], "p1")
        self.assertIn("primary_category", body["recommendations"][0])

        with self.SessionLocal() as db:
            event = db.query(RecommendationEvent).filter(RecommendationEvent.id == body["recommendation_event_id"]).first()
            self.assertIsNotNone(event)
            item = (
                db.query(RecommendationEventItem)
                .filter(
                    RecommendationEventItem.recommendation_event_id == body["recommendation_event_id"],
                    RecommendationEventItem.product_id == "p1",
                )
                .first()
            )
            self.assertIsNotNone(item)
            self.assertEqual(item.rank, 1)

    def test_rating_attribution_obeys_24_hour_window(self) -> None:
        self.register_user()
        headers = self.login_headers()

        with patch(
            "app.routers.recommendations.get_recommendations",
            return_value=(
                "content_seeded",
                "Acilama",
                [
                    {
                        "product_id": "p-window",
                        "product_name": "Window Product",
                        "brand_name": "Brand",
                        "primary_category": "Skincare",
                        "secondary_category": "Sunscreen",
                        "tertiary_category": "Body Sunscreen",
                        "price_usd": 21.0,
                        "rating": 4.4,
                        "score": 0.8,
                    }
                ],
            ),
        ):
            recommendation = self.client.post(
                "/recommendations",
                json={"category": "Body Sunscreen", "top_n": 5},
                headers=headers,
            )

        event_id = recommendation.json()["recommendation_event_id"]
        attributed = self.client.post(
            "/interactions/rate",
            json={
                "product_id": "p-window",
                "rating": 5,
                "recommendation_event_id": event_id,
            },
            headers=headers,
        )
        self.assertEqual(attributed.status_code, 200)
        self.assertTrue(attributed.json()["attributed_within_window"])
        self.assertEqual(attributed.json()["recommendation_event_id"], event_id)
        self.assertEqual(attributed.json()["recommended_rank"], 1)

        with self.SessionLocal() as db:
            event = db.query(RecommendationEvent).filter(RecommendationEvent.id == event_id).first()
            self.assertIsNotNone(event)
            event.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
            db.commit()

        expired = self.client.post(
            "/interactions/rate",
            json={
                "product_id": "p-window",
                "rating": 4,
                "recommendation_event_id": event_id,
            },
            headers=headers,
        )
        self.assertEqual(expired.status_code, 200)
        self.assertFalse(expired.json()["attributed_within_window"])
        self.assertIsNone(expired.json()["recommendation_event_id"])
        self.assertIsNone(expired.json()["recommended_rank"])

    def test_metrics_endpoint_reports_logged_events_and_clicks(self) -> None:
        headers = self.admin_headers()

        with patch(
            "app.routers.recommendations.get_recommendations",
            return_value=(
                "lightfm",
                "Aciklama",
                [
                    {
                        "product_id": "p-metrics",
                        "product_name": "Metric Product",
                        "brand_name": "Brand",
                        "primary_category": "Skincare",
                        "secondary_category": "Sunscreen",
                        "tertiary_category": "Body Sunscreen",
                        "price_usd": 15.0,
                        "rating": 4.7,
                        "score": 0.95,
                    }
                ],
            ),
        ):
            recommendation = self.client.post(
                "/recommendations",
                json={"category": "Body Sunscreen", "top_n": 5},
                headers=headers,
            )

        event_id = recommendation.json()["recommendation_event_id"]

        click_response = self.client.post(
            "/interactions/recommendation-click",
            json={"recommendation_event_id": event_id, "product_id": "p-metrics"},
            headers=headers,
        )
        self.assertEqual(click_response.status_code, 200)
        self.assertTrue(click_response.json()["logged"])

        rate_response = self.client.post(
            "/interactions/rate",
            json={
                "product_id": "p-metrics",
                "rating": 5,
                "recommendation_event_id": event_id,
            },
            headers=headers,
        )
        self.assertEqual(rate_response.status_code, 200)

        metrics = self.client.get("/analytics/recommendation-metrics", headers=headers)
        self.assertEqual(metrics.status_code, 200)
        body = metrics.json()
        self.assertEqual(body["attribution_window_hours"], 24)
        self.assertEqual(body["total_recommendation_events"], 1)
        self.assertEqual(body["total_impressions"], 1)
        self.assertEqual(body["total_clicks"], 1)
        self.assertEqual(body["total_attributed_ratings"], 1)
        self.assertEqual(body["overall_ctr"], 1.0)
        self.assertEqual(body["overall_rating_conversion"], 1.0)
        self.assertEqual(body["overall_positive_rating_rate"], 1.0)
        self.assertEqual(body["average_attributed_rating"], 5.0)
        self.assertEqual(body["model_metrics"][0]["model_used"], "lightfm")

    def test_analytics_endpoints_require_admin_user(self) -> None:
        self.register_user()
        headers = self.login_headers()

        metrics = self.client.get("/analytics/recommendation-metrics", headers=headers)
        self.assertEqual(metrics.status_code, 403)

        offline = self.client.get("/analytics/offline-model-evaluation", headers=headers)
        self.assertEqual(offline.status_code, 403)

    def test_admin_can_access_offline_evaluation_endpoint(self) -> None:
        headers = self.admin_headers()
        response = self.client.get("/analytics/offline-model-evaluation", headers=headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("rows", body)
        self.assertIn("leaders", body)
        self.assertGreater(len(body["rows"]), 0)


if __name__ == "__main__":
    unittest.main()
