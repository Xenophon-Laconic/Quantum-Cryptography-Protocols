# quantum_channel/bob.py
from __future__ import annotations

import zmq
import random
from typing import Literal


from qubits import NQubitChain
from measurement import measure_nqubit_chain, error_rate

# ------------------------------------

QUANTUM_ADDR = "tcp://*:5556"
CLASSICAL_ADDR = "tcp://*:5566"


def remove_different_basis(
    bitstring,
    basis_mask,
):
    return [bit for bit, keep in zip(bitstring, basis_mask) if keep]


def run_bob(
    quantum_addr: str = QUANTUM_ADDR,
    classical_addr: str = CLASSICAL_ADDR,
) -> None:
    context = zmq.Context()

    # ----- Quantum socket -----
    q_socket = context.socket(zmq.PULL)
    q_socket.bind(quantum_addr)

    print("Bob waiting for quantum batch...")

    bob_bits: list[Literal[0, 1]] = []
    bob_bases: list[Literal["Z", "X"]] = []
    incoming_bases: list[Literal["Z", "X"]] = []

    # Quantum phase
    while True:
        msg = q_socket.recv_json()

        if msg.get("type") == "END":
            print("Bob received quantum END.")
            break

        if msg.get("type") != "QUBIT_BATCH":
            raise ValueError(f"Unexpected quantum message type: {msg.get('type')!r}")

        bits = msg["bits"]
        pols = msg["pols"]
        n = len(bits)

        qchain = NQubitChain(bits, pols)
        bob_bases = [random.choice(["Z", "X"]) for _ in range(n)]
        bob_bits = measure_nqubit_chain(qchain, bob_bases)
        incoming_bases = pols

    q_socket.close()
    print("Bob quantum channel done.")

    # ----- Classical socket -----
    c_socket = context.socket(zmq.PULL)
    c_socket.bind(classical_addr)

    print("Bob waiting for classical data from Alice...")

    alice_bits = None
    alice_pols = None

    while True:
        msg = c_socket.recv_json()

        if msg.get("type") == "END":
            print("Bob received classical END.")
            break

        if msg.get("type") == "ALICE_DATA":
            alice_bits = msg["bits"]
            alice_pols = msg["pols"]
        else:
            # Ignore unknown types for now
            pass

    c_socket.close()
    context.destroy()

    if alice_bits is None or alice_pols is None:
        raise RuntimeError("Bob never received ALICE_DATA on classical channel.")

    print("Bob classical channel done. Performing sifting and error estimation...")

    # Sifting: keep only positions where Alice's and Bob's bases match
    if len(alice_bits) != len(bob_bits):
        raise ValueError("Length mismatch between Alice and Bob bitstrings.")

    common_mask = [a == b for a, b in zip(alice_pols, bob_bases)]

    alice_sifted = remove_different_basis(alice_bits, common_mask)
    bob_sifted = remove_different_basis(bob_bits, common_mask)

    eps = 1e-3
    err = error_rate(alice_sifted, bob_sifted)

    print(f"Sifted key length: {len(alice_sifted)}")
    print(f"Error rate on sifted key: {err:.5f}")

    if err > eps:
        print("Secret Key could not be established (too many errors).")
    else:
        key_str = "".join(str(b) for b in alice_sifted)
        print("Key established.")
        print("Key (first 200 bits):", key_str[:200])

    print("Bob finished.")


if __name__ == "__main__":
    run_bob()