first# BB84 Quantum Key Distribution

This repository implements the **BB84 quantum key distribution (QKD) protocol**, first in a simple in‑memory simulation (`bb84.ipynb`), and then extended to a **distributed, ZeroMQ‑based simulation** (`alice.py`, `bob.py`, `eve.py`) that models the quantum communication channel and a subsequent classical post‑processing channel.

The security of BB84 relies fundamentally on the **no‑cloning theorem**: an unknown quantum state cannot be copied perfectly. Any attempt by an eavesdropper (Eve) to gain information about the qubits necessarily disturbs them, introducing detectable errors in the key that Alice and Bob can estimate during classical post‑processing.

---

## The BB84 protocol (overview)

BB84 allows two parties (Alice and Bob) to generate a shared secret key over an insecure channel. Any measurement by an eavesdropper (Eve) disturbs the qubits and introduces errors that Alice and Bob can detect.

The protocol has two main phases:

1. **Quantum transmission phase**
2. **Classical post‑processing phase**

---

## Protocol steps (as implemented here)

### (1) Alice prepares random bits and encodes them in random bases

Alice chooses:

- A random classical bit string  
  $
  a_1, a_2, \dots, a_N \in \{0,1\}
  $
- A random sequence of preparation bases  
  $
  p_1, p_2, \dots, p_N \in \{Z, X\}
  $

She then encodes each bit $a_i$ into a qubit polarised in basis $p_i$:

- **Z basis (rectilinear)**:  
  - `0` → `"-"`  
  - `1` → `"|"`
- **X basis (diagonal)**:  
  - `0` → `"/"`  
  - `1` → `"\\"`

In code:

```python
n = 50000
alice_bitstring = random.choices([0, 1], k=n)
alice_polars = random.choices(["Z", "X"], k=n)

qchain = NQubitChain(alice_bitstring, alice_polars)
```

This is implemented in `qubits.py` via `ZQubit`, `XQubit`, and `NQubitChain`.

---

### (2) Quantum transmission: Alice → Bob (with possible eavesdropping by Eve)

Alice sends her qubits to Bob over a **quantum channel**. In a real system this would be single photons over an optical fiber or free space. Here, I simulate this using **ZeroMQ (zmq)** message passing:

- Alice sends one batch message containing all `(bits, pols)` pairs.
- Eve sits between Alice and Bob and can optionally perform an **intercept‑resend attack**:
  - For each qubit, with probability $p_{\text{intercept}}$, Eve:
    - Chooses a random measurement basis.
    - Measures the qubit (using the same rules as in the notebook).
    - Resends a new qubit to Bob encoded in her basis with her measurement outcome.
  - Otherwise, she forwards the qubit unchanged.
- Bob receives the (possibly altered) qubits and measures each in a randomly chosen basis.

Measurement rules (implemented in `measurement.py`):

- If the measurement basis matches the preparation basis → deterministic outcome (the encoded bit).
- If the bases differ → outcome is random (50/50), and the qubit state is effectively changed.

This reproduces the physics: **Eve’s measurement in the wrong basis introduces errors** that Alice and Bob can later detect. Because of the no‑cloning theorem, Eve cannot do better than this intercept‑resend strategy without introducing disturbances; she cannot copy the qubit perfectly and measure it later after learning the bases.

---

### (3) Bob measures in random bases

Bob independently chooses a random basis for each qubit:

```python
bob_polars = random.choices(["Z", "X"], k=n)
bob_bitstring = measure_nqubit_chain(qchain, bob_polars)
```

In the zmq version, Bob reconstructs the qubit chain from the received batch and calls `measure_nqubit_chain` exactly as in the notebook.

---

### (4) Classical post‑processing: sifting

After the quantum transmission is complete, Alice and Bob use a **classical channel** to compare their bases (but not their bits):

- They keep only the positions where their bases match:
  $
  \{ i \mid p_i^{\text{Alice}} = p_i^{\text{Bob}} \}
  $
- All other positions are discarded.

In code:

```python
common_bases = [a == b for a, b in zip(alice_polars, bob_polars)]

bob_remaining_bits = remove_different_basis(bob_bitstring, common_bases)
alice_remaining_bits = remove_different_basis(alice_bitstring, common_bases)
```

This is the **sifting step**. The remaining bits form the **sifted key**.

---

### (5) Parameter estimation: error rate and eavesdropper detection

Alice and Bob estimate the **error rate** on a subset (or all) of the sifted key:

```python
eps = 0  # or small threshold in realistic scenarios
if error_rate(alice_remaining_bits, bob_remaining_bits) > eps:
    print("Secret Key could not be established")
else:
    key_str = "".join(str(b) for b in alice_remaining_bits)
    print("Key established. Key:", key_str)
```

- If Eve has been eavesdropping (or if there is significant channel noise), the error rate will be elevated.
- If the error rate exceeds a chosen threshold $\varepsilon$, they abort: no secure key can be distilled.
- If the error rate is below the threshold, they proceed (in a full protocol, with error correction and privacy amplification) to obtain a secure key.

In this implementation, Bob performs this check locally after receiving Alice’s data over the classical zmq channel.

---

## Repository structure

```text
BB84/
├── qubits.py           # Qubit types: ZQubit, XQubit, NQubitChain
├── measurement.py      # Measurement utilities: measure_qubit, measure_nqubit_chain, error_rate
├── bb84.ipynb          # Notebook: in-memory BB84 simulation (no communication layer)
├── alice.py            # Alice: quantum + classical channels over zmq
├── bob.py              # Bob: quantum + classical channels, sifting, key decision
├── eve.py              # Eve: optional intercept-resend eavesdropping on quantum channel
└── README.md           # This file
```

### Core modules

- **`qubits.py`**  
  Defines:
  - `ZQubit`: rectilinear (Z‑basis) qubit with values `"-"` and `"|"`.
  - `XQubit`: diagonal (X‑basis) qubit with values `"/"` and `"\\"`.
  - `NQubitChain`: a sequence of qubits encoding a bit string in mixed bases.

- **`measurement.py`**  
  Provides:
  - `measure_qubit(qubit, basis)`: measures a single qubit in a given basis, with correct quantum behavior (deterministic if bases match, random otherwise).
  - `measure_nqubit_chain(chain, bases)`: measures an entire chain with specified bases.
  - `error_rate(a, b)`: computes the bit error rate between two equal‑length bitstrings.

These are used both in the notebook and in the zmq‑based simulation.

---

## Usage

### 1. In‑memory simulation (notebook)

Open `bb84.ipynb` in Jupyter to see a step‑by‑step walkthrough of BB84 with optional eavesdropping, all in a single process. This is useful for understanding the protocol logic.

---

### 2. Distributed simulation with ZeroMQ

This version splits Alice, Bob, and Eve into separate processes communicating over zmq, closer to a real networked scenario.


#### Run order

Start the processes in this order (in separate terminals):

```bash
# Terminal 1: Bob
python bob.py

# Terminal 2: Eve
# Without eavesdropping:
python eve.py
# With eavesdropping (e.g. 30% intercept probability):
python eve.py --eavesdrop --intercept-prob 0.3

# Terminal 3: Alice
python alice.py
```

What happens:

1. **Quantum phase**
   - Alice generates random `bits` and `pols`, constructs an `NQubitChain`, and sends a single `QUBIT_BATCH` message to Eve.
   - Eve optionally performs intercept‑resend attacks and forwards a (possibly modified) batch to Bob.
   - Bob measures the received qubits in random bases.

2. **Classical phase**
   - Alice sends her full `bits` and `pols` to Bob over a separate classical zmq channel (via Eve as a simple forwarder).
   - Bob:
     - Performs sifting (keeps only matching bases).
     - Computes the error rate on the sifted key.
     - Decides whether a secret key can be established and prints the result.

Everything is passed over zmq, so the protocol is not tied to a single process and can be extended to run on multiple machines.

---
