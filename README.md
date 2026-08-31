# 🔗 Phishing URL Detector

A machine learning project that classifies URLs as phishing or legitimate based on structural URL features. Built as a first serious ML project at the intersection of machine learning, data science, and cybersecurity.

## Overview

Phishing attacks trick users into clicking malicious links that steal credentials or install malware. Static blacklists can't keep up with newly created phishing URLs. This project explores whether a machine learning model can flag suspicious URLs based on structural patterns in the URL text alone — before a user ever visits the page.

## Problem Statement

Given a URL, predict whether it is likely phishing or legitimate, using only features that can be computed from the URL string itself (length, character composition, domain structure, TLD reputation), without needing to fetch or render the destination page.

## Motivation

This was my first serious ML project. I wanted something more meaningful than a generic tutorial-following exercise — a project where I understood every decision, not just copied code. I chose the phishing detection problem because it combines a real, understandable security problem with a dataset that has genuine structure to learn from, and because the process of building it forced me to learn core ML methodology (leakage detection, proper evaluation, honest limitations) rather than just chasing a high accuracy number.

## Cybersecurity Context

- **False negatives** (missing a real phishing URL) cause direct user harm — credentials stolen, malware installed. This is the costlier error.
- **False positives** (flagging a safe URL as phishing) cause user annoyance and erode trust in the tool, but the cost is recoverable.
- Given this asymmetry, the project prioritizes **high recall** on the phishing class, while keeping precision reasonable enough that the tool stays usable.
- Attackers constantly generate new phishing URLs, so static blacklists lag behind. A model that generalizes from structural patterns can, in principle, catch novel phishing URLs that no blacklist has seen yet — this is the core argument for using ML here.

## Dataset

- **Source:** PhiUSIIL Phishing URL Dataset (UCI ML Repository)
- **Size:** 235,795 URLs, 56 original columns, binary label (1 = phishing, 0 = legitimate)
- **Scope decision:** the original dataset mixes pure URL-string features (e.g. `URLLength`, `NoOfSubDomain`) with page-content features that require fetching the destination page (e.g. `NoOfImage`, `HasPasswordField`, `NoOfPopup`). Using page-content features would mean the "page has already loaded" by the time we can predict — contradicting the "flag before click" framing. **This v1 uses only the 19 pure URL-string features**, keeping the project's story honest. Page-content features are a documented direction for a v2.

## Methodology

1. **Cleaning:** removed 2,001 duplicate rows out of 235,795.
2. **EDA:** examined class balance (~57% phishing / 43% legitimate), inspected outliers (e.g. one 6,097-character URL), and checked correlations.
3. **Leakage detection:** an initial Logistic Regression model hit 99.97% accuracy — suspiciously perfect. Investigation traced this to a small cluster of features (`URLSimilarityIndex`, `IsHTTPS`, `CharContinuationRate`, `URLCharProb`) that, together, were effectively pre-solving the label. These were dropped, bringing accuracy down to a more defensible ~98.5%.
4. **Train/test split:** 80/20, stratified on the label to preserve class balance in both sets.
5. **Baseline:** a `DummyClassifier` always predicting the majority class scored 57.4% accuracy with 0% precision/recall on the minority class — establishing the floor any real model must clear.
6. **Modeling:** trained and compared Logistic Regression, a single Decision Tree, and a Random Forest.
7. **Scaling bug fix:** an early version applied `StandardScaler` to all features including binary ones (`IsDomainIP`, `HasObfuscation`). Because these binary features have very low variance in the training data, scaling exploded rare `1` values into extreme outlier magnitudes (e.g. a scaled value of +19), causing the model to badly mispredict on real inputs like `192.168.1.1`-style URLs. Fixed by scaling only continuous features via `ColumnTransformer` and leaving binary features untouched.
8. **Interpretation:** examined Logistic Regression coefficients to check whether the model's learned signals matched security intuition.

## Model Comparison

| Model | Accuracy | Precision | Recall | Interpretability | Notes |
|---|---|---|---|---|---|
| Baseline (majority class) | 57.4% | 0% (class 0) | 0% (class 0) | — | Sanity floor only |
| Logistic Regression | 98.5% | 97.6% | 99.9% | High | **Chosen model** |
| Decision Tree (depth 10) | 93.0% | 89–99% | 84–99% | Very high | Weaker than ensemble |
| Random Forest | ~99.9% (rounds to 100%) | ~100% | ~100% | Medium | Verified via 5-fold CV (mean F1 ≈ 0.9965), not a fluke |

**Chosen model: Logistic Regression.** Random Forest performed marginally better and was confirmed consistent via cross-validation, but Logistic Regression was chosen for its interpretability — in a security context, being able to explain *why* a URL was flagged matters as much as raw accuracy, especially for a first project where trustworthy, explainable decisions were a priority over squeezing out the last fraction of a percent.

## Key Findings

- **Long URLs are not automatically phishing.** Rows with `URLLength > 1000` were exclusively legitimate (label 0) in this dataset — contradicting a naive assumption that longer URLs are more suspicious.
- **Domain/TLD reputation was the strongest honest signal.** `TLDLegitimateProb` and a self-engineered `TLD_freq` feature aligned well with security intuition: rare or low-reputation domain extensions pushed predictions toward phishing.
- **Length-related features are highly collinear.** `URLLength`, `NoOfLettersInURL`, `NoOfDigitsInURL`, and `NoOfOtherSpecialCharsInURL` correlate at 0.65–0.96 with each other, since URL length is essentially their sum. This produced unstable, inflated Logistic Regression coefficients (magnitudes up to ±117) — a reminder to trust coefficient *direction* over *magnitude* when features are collinear.
- **A scaling bug silently broke real-world predictions.** Scaling binary features amplified rare values into extreme outliers, causing the model to misclassify obvious phishing patterns (e.g. IP-based domains, subdomain spoofing) in the live demo even though offline test metrics looked fine. Fixing the scaling pipeline immediately improved real-world behavior (e.g. correctly flagging `http://paypal.security-verify.fake-domain.com` after the fix).
- **Raw-IP-based phishing URLs remain a weak spot.** Even after the scaling fix, `IsDomainIP` has a weak learned coefficient because raw-IP URLs are rare in the training data — the demo still misses `http://192.168.1.1/...`-style phishing links. This is a genuine dataset-driven limitation, not a bug.

## Limitations

- Uses only URL-string features by design (v1 scope) — no page-content signals.
- The Streamlit demo's feature extraction is a simplified approximation of the original dataset's extraction pipeline, not an exact match.
- Raw-IP-based phishing detection is weak due to underrepresentation in the training data.
- The dataset may be more cleanly separable than real-world web traffic; real deployment would likely see noisier, harder cases.
- This is a prototype for learning purposes — **not a production security tool**, and should not be relied on as a sole line of defense.

## Demo

A Streamlit app lets you paste a URL and get an instant prediction with a confidence score.

```
streamlit run src/app.py
```

## Installation

```
conda env create -f environment.yml
conda activate phishing-detector
```

## Usage

```
streamlit run src/app.py
```
Then open the local URL shown in the terminal, paste a URL into the input box, and view the prediction.

## Project Structure

```
phishing-url-detector/
├── data/
│   ├── raw/                # original dataset (gitignored)
│   └── processed/          # train/test splits
├── notebooks/
│   ├── 01_eda_and_cleaning.ipynb
│   └── 02_baseline_and_modeling.ipynb
├── src/
│   └── app.py               # Streamlit demo app
├── models/                  # saved model, scaler, feature list, TLD frequency map
├── visualizations/          # saved plots (EDA, coefficients, confusion matrix)
├── environment.yml
├── .gitignore
└── README.md
```

## Technologies Used

Python, pandas, numpy, scikit-learn, matplotlib, seaborn, Streamlit, joblib, conda.

## Future Improvements

- Build a v2 that incorporates page-content features, reframed honestly as a "scan an already-fetched page" tool rather than a pre-click checker.
- Combine the ML model with a hardcoded rule for raw-IP domains, to cover the model's current weak spot.
- Reduce multicollinearity by consolidating length-related features.
- Package the demo as a lightweight browser extension prototype.
- Expand testing with adversarially crafted URLs to probe robustness.

## Lessons Learned

The biggest lesson was that a suspiciously good result (99.97% accuracy) is a signal to investigate, not celebrate — tracing that down to leaking features was the most valuable part of the project. The second was that offline metrics can hide real bugs: the model looked fine in `classification_report`, but a scaling mistake on binary features was quietly breaking real-world predictions until tested through the actual demo app. Building the Streamlit interface and manually testing real URLs surfaced problems that test-set metrics alone did not.