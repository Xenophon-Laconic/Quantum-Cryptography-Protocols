"""Qubit types for a simple BB84-style simulation."""

from __future__ import annotations

from typing import Literal, Sequence


class ZQubit:
    """Rectilinearly polarised photon qubit (Z basis)."""

    qubit_value: Literal["-", "|"]
    basis: Literal["Z"] = "Z"

    def __init__(self, qubit_value: Literal["-", "|"] = "-") -> None:
        self.qubit_value = qubit_value

    def encode_bit(self, bit: Literal[0, 1]) -> None:
        if bit not in (0, 1):
            raise ValueError(f"bit value {bit} not supported, use 0 or 1")
        self.qubit_value = "-" if bit == 0 else "|"

    def decode_bit(self) -> Literal[0, 1]:
        if self.qubit_value == "-":
            return 0
        if self.qubit_value == "|":
            return 1
        raise ValueError(f"invalid ZQubit value: {self.qubit_value!r}")


class XQubit:
    """Diagonally polarised photon qubit (X basis)."""

    qubit_value: Literal["/", "\\"]
    basis: Literal["X"] = "X"

    def __init__(self, qubit_value: Literal["/", "\\"] = "/") -> None:
        self.qubit_value = qubit_value

    def encode_bit(self, bit: Literal[0, 1]) -> None:
        if bit not in (0, 1):
            raise ValueError(f"bit value {bit} not supported, use 0 or 1")
        self.qubit_value = "/" if bit == 0 else "\\"

    def decode_bit(self) -> Literal[0, 1]:
        if self.qubit_value == "/":
            return 0
        if self.qubit_value == "\\":
            return 1
        raise ValueError(f"invalid XQubit value: {self.qubit_value!r}")


class NQubitChain:
    """A chain of qubits encoding a bit string in mixed bases."""

    def __init__(
        self,
        bits: Sequence[Literal[0, 1]],
        polarisations: Sequence[Literal["Z", "X"]],
    ) -> None:
        if len(bits) != len(polarisations):
            raise ValueError(
                f"must have same number of bits as qubits, "
                f"got {len(bits)} bits and {len(polarisations)} qubits"
            )

        self.qubits: list[ZQubit | XQubit] = []
        for polar, bit in zip(polarisations, bits):
            if polar == "Z":
                qubit: ZQubit | XQubit = ZQubit()
                qubit.encode_bit(bit)
                self.qubits.append(qubit)
            elif polar == "X":
                qubit = XQubit()
                qubit.encode_bit(bit)
                self.qubits.append(qubit)
            else:
                raise ValueError(f"expected Z or X polarisation, got {polar!r}")

    def __len__(self) -> int:
        return len(self.qubits)

    def __iter__(self):
        return iter(self.qubits)
