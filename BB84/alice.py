from __future__ import annotations

import zmq
import random
from typing import Literal


from qubits import NQubitChain

# ------------------------------------

QUANTUM_ADDR = "tcp://localhost:5555"
CLASSICAL_ADDR = "tcp://localhost:5565"


def run_alice(
    n: int = 50000,
    quantum_addr: str = QUANTUM_ADDR,
    classical_addr: str = CLASSICAL_ADDR,
) -> None:
    bits: list[Literal[0, 1]] = random.choices([0, 1], k=n)
    pols: list[Literal["Z", "X"]] = random.choices(["Z", "X"], k=n)

    # Consistency check (optional)
    _ = NQubitChain(bits, pols)

    context = zmq.Context()

    # ---------- Quantum channel ----------
    q_socket = context.socket(zmq.PUSH)
    q_socket.connect(quantum_addr)

    print(f"Alice sending quantum batch of {n} qubits...")
    q_socket.send_json({
        "type": "QUBIT_BATCH",
        "bits": list(bits),
        "pols": list(pols),
    })
    q_socket.send_json({"type": "END"})

    q_socket.close()
    print("Alice quantum channel done.")

    # ---------- Classical channel ----------
    c_socket = context.socket(zmq.PUSH)
    c_socket.connect(classical_addr)

    print("Alice sending classical data (bits + pols)...")
    c_socket.send_json({
        "type": "ALICE_DATA",
        "bits": bits,
        "pols": pols,
    })
    c_socket.send_json({"type": "END"})

    c_socket.close()
    context.destroy()
    print("Alice classical channel done. Alice finished.")


if __name__ == "__main__":
    run_alice()