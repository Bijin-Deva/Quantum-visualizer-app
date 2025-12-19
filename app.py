# app.py — Clean, stable, noise-enabled Quantum Circuit Visualizer

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from qiskit import QuantumCircuit, qasm2, ClassicalRegister
from qiskit.quantum_info import DensityMatrix, Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import (
    NoiseModel,
    depolarizing_error,
    amplitude_damping_error,
    phase_damping_error,
    ReadoutError
)

from quantum_utils import (
    get_full_density_matrix_from_circuit,
    get_reduced_density_matrix,
    get_bloch_vector_from_rho,
    purity_from_rho,
)

from bloch_plot import plot_bloch_sphere

# ------------------------------------------------------------
# Page Config
# ------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Quantum State Visualizer")

# ------------------------------------------------------------
# Styling
# ------------------------------------------------------------
st.markdown("""
<style>
.stApp {
    background-image: linear-gradient(to bottom right, #000000, #0D224F);
}
[data-testid="stSidebar"] { background-color: #E6F2FF; }
[data-testid="stSidebar"] * { color: black !important; }
[data-testid="stAppViewContainer"] * { color: white; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Session State Defaults
# ------------------------------------------------------------
defaults = {
    "circuit": None,
    "state_circuit": None,
    "qasm_code": "",
    "user_code": "",
    "counts": None,
    "last_num_qubits": -1,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------------------------------------------------
# Noise Model Builder
# ------------------------------------------------------------
def build_noise_model(depol_p, decay_f, phase_g, ro_01, ro_10):
    noise = NoiseModel()

    if depol_p > 0:
        noise.add_all_qubit_quantum_error(
            depolarizing_error(depol_p, 1),
            ['h', 'x', 'y', 'z', 's', 't', 'cx']
        )

    if decay_f > 0:
        noise.add_all_qubit_quantum_error(
            amplitude_damping_error(decay_f),
            ['h', 'x', 'y', 'z', 's', 't']
        )

    if phase_g > 0:
        noise.add_all_qubit_quantum_error(
            phase_damping_error(phase_g),
            ['h', 'x', 'y', 'z', 's', 't']
        )

    if ro_01 > 0 or ro_10 > 0:
        noise.add_all_qubit_readout_error(
            ReadoutError([
                [1 - ro_01, ro_01],
                [ro_10, 1 - ro_10]
            ])
        )

    return noise

# ------------------------------------------------------------
# Main Title
# ------------------------------------------------------------
st.title("⚛️ Quantum Circuit Simulator & Visualizer")
st.markdown("Write Qiskit code, simulate circuits, visualize Bloch spheres, and apply quantum noise.")

# ------------------------------------------------------------
# Sidebar Controls
# ------------------------------------------------------------
st.sidebar.title("Circuit Controls")

num_qubits = st.sidebar.slider(
    "Number of Qubits",
    min_value=1,
    max_value=5,
    value=2,
    key="num_qubits"
)

if st.sidebar.button("Clear & Reset Circuit"):
    for k in defaults:
        st.session_state[k] = defaults[k]
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Quantum Noise")

enable_noise = st.sidebar.checkbox("Enable Noise", key="enable_noise")

with st.sidebar.expander("Noise Parameters"):
    depol_p = st.sidebar.slider("Depolarization", 0.0, 0.3, 0.0, key="depol_p")
    decay_f = st.sidebar.slider("Amplitude Damping (T1)", 0.0, 0.3, 0.0, key="decay_f")
    phase_g = st.sidebar.slider("Phase Damping (T2)", 0.0, 0.3, 0.0, key="phase_g")
    ro_01 = st.sidebar.slider("|0⟩ → |1⟩", 0.0, 0.3, 0.0, key="ro_01")
    ro_10 = st.sidebar.slider("|1⟩ → |0⟩", 0.0, 0.3, 0.0, key="ro_10")

# ------------------------------------------------------------
# Code Editor
# ------------------------------------------------------------
st.subheader("</> Qiskit Code Editor")

base_code = f"qc = QuantumCircuit({num_qubits}, {num_qubits})\n"

example_code = (
    "qc.h(0)\nqc.cx(0,1)\nqc.measure([0,1],[0,1])\n"
    if num_qubits >= 2 else
    "qc.h(0)\nqc.measure(0,0)\n"
)

default_code = base_code + example_code

if st.session_state.last_num_qubits != num_qubits or not st.session_state.user_code:
    st.session_state.user_code = default_code
    st.session_state.last_num_qubits = num_qubits

user_code = st.text_area("Qiskit Code", st.session_state.user_code, height=250)

# ------------------------------------------------------------
# Run Simulation
# ------------------------------------------------------------
if st.button("Run Simulation"):
    st.session_state.user_code = user_code
    st.session_state.counts = None

    try:
        exec_globals = {"QuantumCircuit": QuantumCircuit, "ClassicalRegister": ClassicalRegister, "np": np}
        exec(user_code, exec_globals)
        qc = exec_globals.get("qc")

        if not isinstance(qc, QuantumCircuit):
            st.error("QuantumCircuit named `qc` not found.")
        else:
            st.session_state.circuit = qc
            st.session_state.qasm_code = qasm2.dumps(qc)

            state_circuit = qc.copy()
            state_circuit.remove_final_measurements(inplace=True)
            st.session_state.state_circuit = state_circuit

            st.success("Simulation successful!")
            st.rerun()

    except Exception as e:
        st.error(f"Code error: {e}")

# ------------------------------------------------------------
# Results
# ------------------------------------------------------------
if st.session_state.circuit is not None:

    st.header("Circuit Diagram")
    st.pyplot(st.session_state.circuit.draw(output="mpl"))

    st.header("OpenQASM")
    st.code(st.session_state.qasm_code, language="qasm")

    # ---------------- Measurement ----------------
    st.header("Measurement Outcomes")

    shots = 1024
    if st.button("Measure & Run"):
        qc_meas = st.session_state.circuit.copy()
        qc_meas.measure_all()

        noise_model = (
            build_noise_model(depol_p, decay_f, phase_g, ro_01, ro_10)
            if enable_noise else None
        )

        sim = AerSimulator(noise_model=noise_model)
        result = sim.run(qc_meas, shots=shots).result()
        st.session_state.counts = result.get_counts()

        st.rerun()

    if st.session_state.counts:
        counts = st.session_state.counts

        fig = go.Figure(go.Bar(
            x=list(counts.keys()),
            y=list(counts.values())
        ))
        st.plotly_chart(fig, use_container_width=True)

        st.metric("Most Probable Outcome", max(counts, key=counts.get))

        with st.expander("Raw Counts"):
            st.json(counts)

    # ---------------- Bloch Spheres ----------------
    st.markdown("---")

    if enable_noise:
        st.info(
            "ℹ️ Bloch spheres show the ideal (noise-free) quantum state. "
            "Noise affects measurement outcomes only."
        )

    st.header("Bloch Sphere Visualizations")

    full_dm = get_full_density_matrix_from_circuit(st.session_state.state_circuit)
    n = st.session_state.state_circuit.num_qubits

    cols = st.columns(n)
    for i in range(n):
        with cols[i]:
            rho = get_reduced_density_matrix(full_dm, n, i)
            bx, by, bz = get_bloch_vector_from_rho(rho)
            purity = purity_from_rho(rho)

            st.plotly_chart(plot_bloch_sphere(bx, by, bz, f"Qubit {i}"), use_container_width=True)
            st.metric("Purity", f"{purity:.4f}")
