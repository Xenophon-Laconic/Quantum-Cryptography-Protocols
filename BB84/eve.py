# quantum_channel/eve.py
from __future__ import annotations

import zmq
import random
import argparse
from typing import Literal


from qubits import NQubitChain
from measurement import measure_qubit

# ------------------------------------

QUANTUM_IN = "tcp://*:5555"
QUANTUM_OUT = "tcp://localhost:5556"

CLASSICAL_IN = "tcp://*:5565"
CLASSICAL_OUT = "tcp://localhost:5566"


def run_eve_quantum(
    recv: zmq.Socket,
    send: zmq.Socket,
    eavesdrop: bool,
    intercept_prob: float,
) -> int:
    intercepted_count = 0

    while True:
        msg = recv.recv_json()  # blocks

        if msg.get("type") == "END":
            send.send_json(msg)
            break

        if msg.get("type") != "QUBIT_BATCH":
            raise ValueError(f"Unexpected quantum message type: {msg.get('type')!r}")

        bits = msg["bits"]
        pols = msg["pols"]
        n = len(bits)

        if eavesdrop:
            qchain = NQubitChain(bits, pols)
            new_bits = []
            new_pols = []

            for i, (bit_alice, pol_alice) in enumerate(zip(bits, pols)):
                if random.random() < intercept_prob:
                    basis_eve: Literal["Z", "X"] = random.choice(["Z", "X"])
                    q = qchain.qubits[i]
                    eve_bit = measure_qubit(q, basis_eve)

                    new_bits.append(eve_bit)
                    new_pols.append(basis_eve)
                    intercepted_count += 1
                else:
                    new_bits.append(bit_alice)
                    new_pols.append(pol_alice)

            msg = {
                "type": "QUBIT_BATCH",
                "bits": new_bits,
                "pols": new_pols,
            }

        send.send_json(msg)

    return intercepted_count


def run_eve_classical(recv: zmq.Socket, send: zmq.Socket) -> None:
    # For now, Eve just forwards classical data unchanged.
    while True:
        msg = recv.recv_json()  # blocks

        if msg.get("type") == "END":
            send.send_json(msg)
            break

        # Forward whatever Alice sent (ALICE_DATA or future types)
        send.send_json(msg)


def run_eve(
    quantum_in: str = QUANTUM_IN,
    quantum_out: str = QUANTUM_OUT,
    classical_in: str = CLASSICAL_IN,
    classical_out: str = CLASSICAL_OUT,
    eavesdrop: bool = False,
    intercept_prob: float = 0.3,
) -> None:
    context = zmq.Context()

    # ----- Quantum sockets -----
    q_recv = context.socket(zmq.PULL)
    q_recv.bind(quantum_in)

    q_send = context.socket(zmq.PUSH)
    q_send.connect(quantum_out)

    # ----- Classical sockets -----
    c_recv = context.socket(zmq.PULL)
    c_recv.bind(classical_in)

    c_send = context.socket(zmq.PUSH)
    c_send.connect(classical_out)

    print(f"Eve running (eavesdrop={eavesdrop}, intercept_prob={intercept_prob})")

    # Quantum phase
    intercepted = run_eve_quantum(q_recv, q_send, eavesdrop, intercept_prob)
    q_recv.close()
    q_send.close()
    print(f"Eve quantum channel done (intercepted ~{intercepted} qubits).")

    # Classical phase
    run_eve_classical(c_recv, c_send)
    c_recv.close()
    c_send.close()

    context.destroy()
    print("Eve classical channel done. Eve finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--eavesdrop", action="store_true")
    parser.add_argument("--intercept-prob", type=float, default=0.3)
    args = parser.parse_args()

    run_eve(eavesdrop=args.eavesdrop, intercept_prob=args.intercept_prob)