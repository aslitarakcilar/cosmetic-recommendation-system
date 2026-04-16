# Thesis Rebuild Plan

## Current Situation

This repository already contains valuable work:

- `data_raw/`: original Sephora product and review files
- `data_interim/products_clean.csv`: cleaned product table
- `data_interim/reviews_cf_last.csv`, `reviews_cf_mean.csv`, `reviews_cf_first.csv`: interaction tables for collaborative filtering
- `notebooks/01_data_loading.ipynb`: preprocessing and profile feature construction
- `notebooks/02_evaluation.ipynb`: train/test split, baseline models, evaluation metrics
- `notebooks/03_sbert_model.ipynb`: SBERT-based content representation experiment

The main problem is not "no progress". The main problem is that:

- preprocessing, modeling, experimentation, and demo logic are mixed together
- notebook names do not reflect the thesis story clearly
- profile-based modeling is partially prepared but not evaluated in a clean thesis pipeline
- backend/frontend work is mixed into the same mental space as the thesis experiments

## Decision

Do not throw everything away.

Keep the preprocessing outputs and evaluation ideas.
Rebuild the project structure around a cleaner thesis pipeline.

## Recommended Thesis Scope

The thesis should compare these recommendation approaches:

1. Popularity baseline
2. Profile-based recommendation
3. Content-based recommendation
4. Collaborative filtering
5. Hybrid recommendation

For each model, report at least:

- Precision@10
- Hit Rate@10
- NDCG@10

Optional:

- Recall@10
- Coverage

## Clean Project Structure

Recommended structure:

```text
Tez_Sephora/
  data_raw/
  data_interim/
  data_processed/
  notebooks/
    01_data_understanding.ipynb
    02_preprocessing.ipynb
    03_profile_based_model.ipynb
    04_content_based_model.ipynb
    05_collaborative_filtering.ipynb
    06_hybrid_model.ipynb
    07_evaluation_and_comparison.ipynb
    08_demo_cases.ipynb
  outputs/
    figures/
    tables/
  app/
  frontend/
  README.md
```

## What Each Notebook Should Contain

### `01_data_understanding.ipynb`

Only EDA and dataset understanding:

- dataset dimensions
- column descriptions
- missing value analysis
- duplicate analysis
- rating distribution
- category distribution
- user interaction count distribution

No model training here.

### `02_preprocessing.ipynb`

Only preprocessing and saved artifacts:

- clean product table
- parse `ingredients` and `highlights`
- create `product_text`
- merge review files
- convert timestamps
- create `reviews_cf_last`, `reviews_cf_mean`, `reviews_cf_first`
- create `product_profile.csv`

At the end:

- save all reusable outputs to `data_interim/`
- add a short "Produced Files" section

### `03_profile_based_model.ipynb`

Only profile-based recommendation:

- define user profile attributes used in the thesis
- build product profile scores by `skin_type` and `skin_tone`
- define fallback logic
- show a few sample recommendations

Important:
This notebook should end with a reusable recommendation function and, if possible, saved profile artifacts.

### `04_content_based_model.ipynb`

Only content-based recommendation:

- TF-IDF baseline first
- optionally SBERT as an advanced experiment
- explain product text representation
- compute similarity
- show sample item-to-item recommendations

Important:
Treat TF-IDF and SBERT as two variants of the same family, not as unrelated work.

### `05_collaborative_filtering.ipynb`

Only collaborative filtering:

- train/test-ready interaction data
- user-item matrix
- SVD or another chosen CF approach
- top-N recommendation function
- sample recommendations for known users

### `06_hybrid_model.ipynb`

Only hybrid logic:

- define which components are combined
- normalize component scores
- test multiple `alpha` values
- explain why final `alpha` is chosen

### `07_evaluation_and_comparison.ipynb`

Only evaluation:

- same train/test split for all models
- same relevance definition
- same `k`
- compute metrics for all models
- produce final comparison tables and plots
- save final results to `outputs/`

This notebook should be the most thesis-friendly one.

### `08_demo_cases.ipynb`

Only qualitative examples:

- example user profiles
- example known users
- sample recommended products
- short interpretation of why the system recommends them

This helps a lot during advisor meetings and thesis writing.

## What To Freeze For Now

These parts are not the thesis core right now:

- `frontend/`
- user registration and authentication in `app/`
- SQLite user table work

Do not delete them yet.
But do not let them drive the thesis structure.

## Immediate Action Plan

### Phase 1: Stabilize

1. Keep `data_interim/` outputs as the current baseline.
2. Rename or recreate notebooks with the clean sequence above.
3. Move duplicated cells out of notebooks as much as possible.

### Phase 2: Make Models Thesis-Ready

1. Finish profile-based model cleanly.
2. Separate TF-IDF content model from SBERT experiment.
3. Rebuild collaborative filtering notebook with only CF logic.
4. Rebuild hybrid notebook using finalized content and CF functions.

### Phase 3: Make Evaluation Defensible

1. Use one fixed train/test split.
2. Use one relevance rule such as `rating >= 4`.
3. Evaluate all models under the same conditions.
4. Export final result tables.

### Phase 4: Make It Explainable

1. Add markdown explanations before each important block.
2. Add a short summary section at the end of every notebook.
3. Add one notebook with illustrative recommendation examples.

## Practical Recommendation

Start again structurally, not from zero data.

That means:

- do not discard `products_clean.csv`
- do not discard `reviews_cf_*.csv`
- do not discard your current metric setup
- do rebuild the notebooks from a clean order

## Minimum Thesis Story

If time becomes tight, the safest strong story is:

1. Build preprocessing pipeline
2. Build popularity baseline
3. Build profile-based model
4. Build TF-IDF content-based model
5. Build SVD collaborative filtering model
6. Build hybrid model
7. Compare with Precision@10, Hit Rate@10, NDCG@10
8. Discuss why hybrid performs best and where it still fails

## Current Evidence That The Project Is Salvageable

Based on the current repository:

- preprocessing outputs already exist
- model comparison output already exists in `outputs/model_comparison_final.csv`
- collaborative filtering and hybrid evaluation logic already exist
- content-based logic already exists in both TF-IDF and SBERT forms

So the project is messy, but not broken.
The right move is a controlled rebuild, not a full reset.
