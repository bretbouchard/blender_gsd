"""
4-Point Direct Linear Transform (DLT) alignment for non-planar/multi-surface projection targets.

Adapted from Compify's camera_align.py technique for physical projector mapping.

This implementation uses numpy for SVD decomposition.
"""

import math
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

from .alignment import Vector3, Matrix3x3, Matrix4x4, AlignmentResult


@dataclass
class DLTResult:
    """Result of 4-point DLT alignment."""
    projection_matrix: List[List[float]]  # P as 3x4 matrix
    intrinsics: List[List[float]]   # K matrix (3x3)
    rotation: List[List[float]]  # R matrix (3x3)
    translation: Tuple[float, float, float]
    error: float = 0.0


def build_dlt_matrix(
    image_points: List[Tuple[float, float]],
    world_points: List[Tuple[float, float, float]]
) -> np.ndarray:
    """
    Build the DLT coefficient matrix A for solving Ap = 0.

    For each correspondence (u_i, v_i) <-> (X_i, Y_i, Z_i):
    [X_i, Y_i, Z_i, 1, 0, 0, 0, 0, -u_i*X_i, -u_i*Y_i, -u_i*Z_i, -u_i]
    [0, 0, 0, 0, X_i, Y_i, Z_i, 1, -v_i*X_i, -v_i*Y_i, -v_i*Z_i, -v_i]

    Stack all correspondences and solve via SVD.

    Args:
        image_points: 2D points in projector UV space (0-1 range)
        world_points: 3D points in world space (meters)

    Returns:
        DLT coefficient matrix A (2n x 12)
    """
    n = len(image_points)
    A = np.zeros((2 * n, 12))

    for i, ((u, v), (X, Y, Z)) in enumerate(zip(image_points, world_points)):
        A[2*i] = [X, Y, Z, 1, 0, 0, 0, 0, -u*X, -u*Y, -u*Z, -u]
        A[2*i+1] = [0, 0, 0, 0, X, Y, Z, 1, -v*X, -v*Y, -v*Z, -v]

    return A


def solve_dlt(A: np.ndarray) -> np.ndarray:
    """
    Solve DLT system via SVD.

    The solution p is the right singular vector corresponding to
    the smallest singular value.

    Args:
        A: DLT coefficient matrix

    Returns:
        Projection matrix P (3x4)
    """
    U, S, Vh = np.linalg.svd(A)
    p = Vh[-1]  # Last row of Vh
    return p.reshape(3, 4)


def rq_decomposition(M: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    RQ decomposition: M = R @ Q where R is upper triangular.

    Implemented using QR decomposition with reversed columns/rows.

    Args:
        M: 3x3 matrix

    Returns:
        (R, Q) - Upper triangular R and orthogonal Q
    """
    # Reverse columns
    M_rev = M[:, ::-1]

    # QR decomposition
    Q_rev, R_rev = np.linalg.qr(M_rev.T)
    Q_rev = Q_rev.T
    R_rev = R_rev.T

    # Reverse back
    R = R_rev[:, ::-1]
    Q = Q_rev[::-1, :]

    # Ensure positive diagonal
    D = np.diag(np.sign(np.diag(R)))
    R = R @ D
    Q = D @ Q

    return R, Q


def decompose_projection_matrix(P: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Decompose projection matrix P = K [R | t].

    Uses RQ decomposition to separate K (upper triangular) from [R | t].

    Args:
        P: 3x4 projection matrix

    Returns:
        K, R, t - Intrinsics (3x3), rotation matrix (3x3), translation vector (3,)
    """
    # Extract M = K*R (first 3x3 of P)
    M = P[:, :3]

    # RQ decomposition: M = K @ R
    K, R = rq_decomposition(M)

    # Normalize K so K[2,2] = 1
    K = K / K[2, 2]

    # Extract t from last column of P
    t = np.linalg.inv(K) @ P[:, 3]

    return K, R, t


def compute_dlt_error(
    projector_points: List[Vector3],
    world_points: List[Vector3],
    P: np.ndarray
) -> float:
    """
    Compute RMS reprojection error in projector UV pixels.

    Args:
        projector_points: Points in projector UV space (0-1 range)
        world_points: Corresponding points in world space (3D)
        P: Projection matrix (3x4)

    Returns:
        RMS reprojection error
    """
    errors = []
    for proj_pt, world_pt in zip(projector_points, world_points):
        # Project world point
        X = np.array([world_pt.x, world_pt.y, world_pt.z, 1])
        projected = P @ X
        projected = projected[:2] / projected[2]  # Normalize

        # Compare to actual
        actual = np.array([proj_pt.x, proj_pt.y])
        error = np.linalg.norm(projected - actual)
        errors.append(error)

    return math.sqrt(np.mean(np.array(errors) ** 2))


def four_point_dlt_alignment(
    projector_points: List[Vector3],
    world_points: List[Vector3]
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """
    Compute projector transform from 4+ correspondences using DLT.

    Args:
        projector_points: 4+ points in projector UV space (0-1 range)
        world_points: 4+ corresponding points in world space (meters)

    Returns:
        K, R, t, error - Intrinsics, rotation, translation, RMS error
    """
    if len(projector_points) < 4 or len(world_points) < 4:
        raise ValueError("At least 4 points required for DLT alignment")

    # Convert to numpy arrays
    uv = [(p.x, p.y) for p in projector_points]
    xyz = [(p.x, p.y, p.z) for p in world_points]

    # Build and solve DLT
    A = build_dlt_matrix(uv, xyz)
    P = solve_dlt(A)

    # Decompose
    K, R, t = decompose_projection_matrix(P)

    # Compute error
    error = compute_dlt_error(projector_points, world_points, P)

    return K, R, t, error
