from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from app.services.recommendation_service import get_recommendations


def make_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "product_id": "p1",
                "product_name": "Test Product",
                "brand_name": "Test Brand",
                "primary_category": "Skincare",
                "secondary_category": "Sunscreen",
                "tertiary_category": "Body Sunscreen",
                "price_usd": 12.0,
                "rating": 4.5,
                "score": 0.8,
            }
        ]
    )


class RecommendationRoutingTests(unittest.TestCase):
    def test_known_lightfm_user_uses_lightfm_first(self) -> None:
        with (
            patch("app.services.recommendation_service.lightfm_has_user", return_value=True),
            patch("app.services.recommendation_service.user_has_app_history", return_value=True),
            patch("app.services.recommendation_service.lightfm_recommend", return_value=make_df()) as lightfm_mock,
            patch("app.services.recommendation_service.content_seeded_recommend") as content_mock,
        ):
            path, _, items = get_recommendations(
                category="Body Sunscreen",
                top_n=10,
                user_id=123,
                skin_type="dry",
                skin_tone="light",
                db=object(),  # type: ignore[arg-type]
            )

        self.assertEqual(path, "lightfm")
        self.assertEqual(len(items), 1)
        lightfm_mock.assert_called_once()
        content_mock.assert_not_called()

    def test_app_history_beats_lightfm_cold_start(self) -> None:
        with (
            patch("app.services.recommendation_service.lightfm_has_user", return_value=False),
            patch("app.services.recommendation_service.lightfm_supports_cold_start", return_value=True),
            patch("app.services.recommendation_service.user_has_app_history", return_value=True),
            patch("app.services.recommendation_service.get_user_interactions", return_value=[]),
            patch("app.services.recommendation_service.get_top_rated_product_ids", side_effect=[["p1"], ["p1"]]),
            patch("app.services.recommendation_service.content_seeded_recommend", return_value=make_df()) as content_mock,
            patch("app.services.recommendation_service.lightfm_recommend") as lightfm_mock,
        ):
            path, _, _ = get_recommendations(
                category="Body Sunscreen",
                top_n=10,
                user_id=123,
                skin_type="dry",
                skin_tone="light",
                db=object(),  # type: ignore[arg-type]
            )

        self.assertEqual(path, "content_seeded")
        content_mock.assert_called_once()
        lightfm_mock.assert_not_called()

    def test_cold_start_lightfm_used_for_new_user_without_history(self) -> None:
        with (
            patch("app.services.recommendation_service.lightfm_has_user", return_value=False),
            patch("app.services.recommendation_service.lightfm_supports_cold_start", return_value=True),
            patch("app.services.recommendation_service.user_has_app_history", return_value=False),
            patch("app.services.recommendation_service.lightfm_recommend", return_value=make_df()) as lightfm_mock,
            patch("app.services.recommendation_service.profile_recommend") as profile_mock,
        ):
            path, _, _ = get_recommendations(
                category="Body Sunscreen",
                top_n=10,
                user_id=123,
                skin_type="dry",
                skin_tone="light",
                db=object(),  # type: ignore[arg-type]
            )

        self.assertEqual(path, "lightfm")
        lightfm_mock.assert_called_once()
        profile_mock.assert_not_called()

    def test_profile_fallback_when_cold_start_unavailable(self) -> None:
        with (
            patch("app.services.recommendation_service.lightfm_has_user", return_value=False),
            patch("app.services.recommendation_service.lightfm_supports_cold_start", return_value=False),
            patch("app.services.recommendation_service.user_has_app_history", return_value=False),
            patch("app.services.recommendation_service.profile_recommend", return_value=make_df()) as profile_mock,
            patch("app.services.recommendation_service.lightfm_recommend") as lightfm_mock,
        ):
            path, _, _ = get_recommendations(
                category="Body Sunscreen",
                top_n=10,
                user_id=123,
                skin_type="dry",
                skin_tone="light",
                db=object(),  # type: ignore[arg-type]
            )

        self.assertEqual(path, "profile")
        profile_mock.assert_called_once()
        lightfm_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
