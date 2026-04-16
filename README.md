# Personalized Cosmetic Recommendation System

Computer Engineering Graduation Thesis

Dataset: Sephora Products and Reviews

Goal: Build a hybrid recommender system using
- profile-based recommendation
- collaborative filtering
- content-based filtering

Current clean-pipeline model family:
- profile-based recommendation
- TF-IDF content-based recommendation
- SBERT content-based recommendation
- TruncatedSVD collaborative filtering
- LightFM collaborative filtering
- dynamic CF-first rerank hybrid

## Notebook Flow

The thesis notebooks are now separated by responsibility:

- `notebooks/01_data_understanding.ipynb`
- `notebooks/02_preprocessing.ipynb`
- `notebooks/03_profile_based_model.ipynb`
- `notebooks/04_content_based_model.ipynb`
- `notebooks/05_collaborative_filtering.ipynb`
- `notebooks/06_hybrid_model.ipynb`
- `notebooks/07_evaluation_and_comparison.ipynb`
- `notebooks/08_demo_cases.ipynb`

Previous mixed notebooks were preserved as:

- `notebooks/legacy_01_data_loading.ipynb`
- `notebooks/legacy_02_evaluation.ipynb`
- `notebooks/legacy_03_sbert_model.ipynb`
