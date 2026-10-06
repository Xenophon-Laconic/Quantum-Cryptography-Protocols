"""Measurement utilities for qubit simulations."""

from __future__ import annotations

import random
from typing import Literal, Sequence

from qubits import ZQubit, XQubit, NQubitChain


def measure_qubit(
    qubit: XQubit | ZQubit,
    basis: Literal["Z", "X"],
) -> Literal[0, 1]:
    """
    Measure a single qubit in the given basis.

    - If the measurement basis matches the qubit's preparation basis,
      returns the encoded bit deterministically.
    - If the bases differ, changes the qubit state and returns a random bit (50/50) 
    """
    if basis not in ("Z", "X"):
        raise ValueError(f"basis must be 'Z' or 'X', got {basis!r}")

    if qubit.basis != basis:
        new_bit = random.randint(0, 1)
        qubit.encode_bit(new_bit)
        return new_bit
    return qubit.decode_bit()


def measure_nqubit_chain(
    nqubit_chain: NQubitChain,
    bases: Sequence[Literal["Z", "X"]],
) -> list[Literal[0, 1]]:
    """
    Measure all qubits in a chain with the specified measurement bases.

    `bases` must have the same length as the qubit chain.
    """
    if len(bases) != len(nqubit_chain):
        raise ValueError(
            f"number of bases ({len(bases)}) must match number of qubits "
            f"({len(nqubit_chain)})"
        )

    result: list[Literal[0, 1]] = []
    for q, b in zip(nqubit_chain.qubits, bases):
        if b not in ("Z", "X"):
            raise ValueError(f"basis must be 'Z' or 'X', got {b!r}")
        result.append(measure_qubit(q, b))
    return result


def error_rate(
    alice_bitstring: Sequence[Literal[0, 1]],
    bob_bitstring: Sequence[Literal[0, 1]],
) -> float:
    """
    Compute the bit error rate between two equal-length bitstrings.

    Returns the fraction of positions where the bits differ.
    """
    if len(alice_bitstring) != len(bob_bitstring):
        raise ValueError(
            f"bitstrings must have equal length, got "
            f"{len(alice_bitstring)} and {len(bob_bitstring)}"
        )
    if len(alice_bitstring) == 0:
        return 0.0

    matches = sum(a == b for a, b in zip(alice_bitstring, bob_bitstring))
    return 1.0 - matches / len(alice_bitstring)
