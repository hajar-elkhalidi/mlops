"""
Tests unitaires des composants ML (matrice user-item, recommandation).
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

sys.path.append(str(Path(__file__).parent.parent.parent / "ml" / "src"))

from train import evaluate, precision_at_k  # noqa: E402


def test_evaluate_perfect_predictions():
    y_true = np.array([3.0, 4.0, 5.0])
    y_pred = np.array([3.0, 4.0, 5.0])
    metrics = evaluate(y_true, y_pred)
    assert metrics["rmse"] == pytest.approx(0.0)
    assert metrics["mae"] == pytest.approx(0.0)


def test_evaluate_known_error():
    y_true = np.array([3.0, 4.0])
    y_pred = np.array([4.0, 5.0])
    metrics = evaluate(y_true, y_pred)
    assert metrics["rmse"] == pytest.approx(1.0)
    assert metrics["mae"] == pytest.approx(1.0)


def test_precision_at_k_with_relevant_items():
    matrix_true = csr_matrix(np.array([[5.0, 0.0, 4.5, 0.0]]))
    matrix_pred = np.array([[0.9, 0.1, 0.8, 0.2]])
    precision = precision_at_k(matrix_true, matrix_pred, k=2)
    assert 0.0 <= precision <= 1.0


def test_precision_at_k_no_ratings_returns_zero():
    matrix_true = csr_matrix(np.zeros((1, 4)))
    matrix_pred = np.array([[0.1, 0.2, 0.3, 0.4]])
    precision = precision_at_k(matrix_true, matrix_pred, k=2)
    assert precision == 0.0
