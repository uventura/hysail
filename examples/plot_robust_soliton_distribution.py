#!/usr/bin/env python3

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plot the robust soliton distribution for a given K, c and delta."
    )
    parser.add_argument(
        "--k", type=int, default=100, help="Number of source symbols (K)."
    )
    parser.add_argument(
        "--c",
        type=float,
        default=0.2,
        help="Robust soliton constant c (recommended around 0.1 to 0.2).",
    )
    parser.add_argument(
        "--delta",
        type=float,
        default=0.01,
        help="Failure probability delta (e.g. 0.01).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output PNG path (e.g. examples/rsd.png).",
    )
    return parser


def validate_args(k: int, c: float, delta: float) -> None:
    if k < 2:
        raise ValueError("K must be at least 2.")
    if c <= 0:
        raise ValueError("c must be greater than 0.")
    if not (0 < delta < 1):
        raise ValueError("delta must be between 0 and 1.")


def main() -> None:
    args = build_parser().parse_args()
    validate_args(args.k, args.c, args.delta)

    from hysail.utils.operators import robust_soliton_distribution

    mu = robust_soliton_distribution(args.k, c=args.c, delta=args.delta)
    degrees = np.arange(1, len(mu))
    probabilities = mu[1:]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(degrees, probabilities, width=0.9, color="#2a9d8f", edgecolor="#1f6f66")
    fig.suptitle("Robust Soliton Distribution Example", fontsize=14, weight="bold")
    ax.set_title(f"c={args.c}, delta={args.delta}", fontsize=10, pad=8)
    ax.set_xlabel("Degree")
    ax.set_ylabel("Probability")
    ax.set_xlim(0.5, args.k + 0.5)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix.lower() != ".png":
            raise ValueError("Output file must have a .png extension.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        print(f"Saved plot to: {output_path}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
