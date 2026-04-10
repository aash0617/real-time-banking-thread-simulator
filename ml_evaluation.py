"""
Standalone ML evaluation module for train/test diagnostics.

This is intentionally separate from thread_model.py, which is a concurrency model
comparison module and not a machine-learning predictor.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)


RANDOM_SEED = 42


@dataclass
class ClassificationMetrics:
    train_accuracy: float
    test_accuracy: float
    train_precision: float
    test_precision: float
    train_recall: float
    test_recall: float
    train_f1: float
    test_f1: float


@dataclass
class RegressionMetrics:
    train_mae: float
    test_mae: float
    train_mse: float
    test_mse: float
    train_rmse: float
    test_rmse: float
    train_r2: float
    test_r2: float


@dataclass
class FitDiagnosis:
    classification_status: str
    regression_status: str


def build_synthetic_dataset(
    n_samples: int,
    seed: int,
    profile: str = "train",
):
    """Build a reproducible synthetic banking dataset for classification + regression."""
    rng = np.random.default_rng(seed)

    if profile == "train":
        amount = rng.integers(100, 10000, n_samples)
        processing_ms = rng.integers(100, 2000, n_samples)
        queue_depth = rng.integers(1, 30, n_samples)
        noise_flip_rate = 0.05
        latency_noise = 40
    else:
        # Slight distribution shift so test data is genuinely different.
        amount = rng.integers(150, 12000, n_samples)
        processing_ms = rng.integers(120, 2300, n_samples)
        queue_depth = rng.integers(1, 36, n_samples)
        noise_flip_rate = 0.06
        latency_noise = 55

    priority = rng.integers(1, 6, n_samples)
    txn_type = rng.integers(0, 2, n_samples)  # 0=deposit, 1=withdraw
    account_balance = rng.integers(1000, 20000, n_samples)

    # Classification target: transaction success/failure.
    # Deposits always succeed. Withdrawals fail when amount is too high for balance.
    y_success = np.where(txn_type == 0, 1, (amount <= account_balance).astype(int))

    # Inject realistic noise so the task is non-trivial.
    noisy_fail_mask = rng.random(n_samples) < noise_flip_rate
    y_success = np.where(noisy_fail_mask, 1 - y_success, y_success)

    # Regression target: completion latency in ms.
    y_latency_ms = (
        0.65 * processing_ms
        + 18.0 * queue_depth
        - 35.0 * priority
        + 0.004 * amount
        + rng.normal(0, latency_noise, n_samples)
    )
    y_latency_ms = np.clip(y_latency_ms, a_min=50, a_max=None)

    features = np.column_stack(
        [
            amount,
            processing_ms,
            queue_depth,
            priority,
            txn_type,
            account_balance,
        ]
    )

    feature_names = [
        "amount",
        "processing_ms",
        "queue_depth",
        "priority",
        "txn_type_withdraw",
        "account_balance",
    ]

    return features, y_success, y_latency_ms, feature_names


def evaluate_classification(x_train, x_test, y_train, y_test) -> ClassificationMetrics:
    clf = RandomForestClassifier(n_estimators=250, random_state=RANDOM_SEED)
    clf.fit(x_train, y_train)

    train_pred = clf.predict(x_train)
    test_pred = clf.predict(x_test)

    return ClassificationMetrics(
        train_accuracy=accuracy_score(y_train, train_pred),
        test_accuracy=accuracy_score(y_test, test_pred),
        train_precision=precision_score(y_train, train_pred, zero_division=0),
        test_precision=precision_score(y_test, test_pred, zero_division=0),
        train_recall=recall_score(y_train, train_pred, zero_division=0),
        test_recall=recall_score(y_test, test_pred, zero_division=0),
        train_f1=f1_score(y_train, train_pred, zero_division=0),
        test_f1=f1_score(y_test, test_pred, zero_division=0),
    )


def evaluate_regression(x_train, x_test, y_train, y_test) -> RegressionMetrics:
    reg = RandomForestRegressor(n_estimators=250, random_state=RANDOM_SEED)
    reg.fit(x_train, y_train)

    train_pred = reg.predict(x_train)
    test_pred = reg.predict(x_test)

    train_mse = mean_squared_error(y_train, train_pred)
    test_mse = mean_squared_error(y_test, test_pred)

    return RegressionMetrics(
        train_mae=mean_absolute_error(y_train, train_pred),
        test_mae=mean_absolute_error(y_test, test_pred),
        train_mse=train_mse,
        test_mse=test_mse,
        train_rmse=float(np.sqrt(train_mse)),
        test_rmse=float(np.sqrt(test_mse)),
        train_r2=r2_score(y_train, train_pred),
        test_r2=r2_score(y_test, test_pred),
    )


def diagnose_fit(
    cls_metrics: ClassificationMetrics, reg_metrics: RegressionMetrics
) -> FitDiagnosis:
    cls_gap = cls_metrics.train_accuracy - cls_metrics.test_accuracy
    reg_gap = reg_metrics.train_r2 - reg_metrics.test_r2

    if cls_metrics.train_accuracy < 0.75 and cls_metrics.test_accuracy < 0.75:
        cls_status = "Underfitting"
    elif cls_gap > 0.08:
        cls_status = "Overfitting"
    else:
        cls_status = "Good fit"

    if reg_metrics.train_r2 < 0.60 and reg_metrics.test_r2 < 0.60:
        reg_status = "Underfitting"
    elif reg_gap > 0.15:
        reg_status = "Overfitting"
    else:
        reg_status = "Good fit"

    return FitDiagnosis(classification_status=cls_status, regression_status=reg_status)


def run_ml_evaluation():
    x_train, y_cls_train, y_reg_train, feature_names = build_synthetic_dataset(
        n_samples=1600,
        seed=RANDOM_SEED,
        profile="train",
    )
    x_test, y_cls_test, y_reg_test, _ = build_synthetic_dataset(
        n_samples=400,
        seed=RANDOM_SEED + 999,
        profile="test",
    )

    cls_metrics = evaluate_classification(x_train, x_test, y_cls_train, y_cls_test)
    reg_metrics = evaluate_regression(x_train, x_test, y_reg_train, y_reg_test)
    fit = diagnose_fit(cls_metrics, reg_metrics)

    print("\n" + "=" * 64)
    print("ML EVALUATION REPORT (TRAIN vs TEST)")
    print("=" * 64)
    print(f"Train Samples: {x_train.shape[0]} | Test Samples: {x_test.shape[0]} | Features: {len(feature_names)}")
    print("Data source: independently generated train and test sets")
    print(f"Feature set: {', '.join(feature_names)}")

    print("\n[Classification Metrics]")
    print(f"Train Accuracy : {cls_metrics.train_accuracy:.4f}")
    print(f"Test Accuracy  : {cls_metrics.test_accuracy:.4f}")
    print(f"Train Precision: {cls_metrics.train_precision:.4f}")
    print(f"Test Precision : {cls_metrics.test_precision:.4f}")
    print(f"Train Recall   : {cls_metrics.train_recall:.4f}")
    print(f"Test Recall    : {cls_metrics.test_recall:.4f}")
    print(f"Train F1       : {cls_metrics.train_f1:.4f}")
    print(f"Test F1        : {cls_metrics.test_f1:.4f}")

    print("\n[Regression Metrics]")
    print(f"Train MAE : {reg_metrics.train_mae:.4f}")
    print(f"Test MAE  : {reg_metrics.test_mae:.4f}")
    print(f"Train MSE : {reg_metrics.train_mse:.4f}")
    print(f"Test MSE  : {reg_metrics.test_mse:.4f}")
    print(f"Train RMSE: {reg_metrics.train_rmse:.4f}")
    print(f"Test RMSE : {reg_metrics.test_rmse:.4f}")
    print(f"Train R2  : {reg_metrics.train_r2:.4f}")
    print(f"Test R2   : {reg_metrics.test_r2:.4f}")

    print("\n[Fit Diagnosis]")
    print(f"Classification: {fit.classification_status}")
    print(f"Regression    : {fit.regression_status}")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    run_ml_evaluation()
