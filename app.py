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


# NOTE: You will need to have your 'quantum_utils.py' and 'bloch_plot.py' files
# in the same directory for these imports to work.
@@ -15,6 +23,37 @@
    get_bloch_vector_from_rho,
    purity_from_rho,
)
def build_noise_model():
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

from bloch_plot import plot_bloch_sphere

# --- Page and Session State Setup ---
@@ -38,12 +77,12 @@
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] .stMarkdown p { color: white !important; }
[data-testid="stSidebar"] { background-color: #0A193D; }
[data-testid="stSidebar"] { background-color: #E6F2FF; }
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: white !important; }
[data-testid="stSidebar"] h3 { color: black !important; }
[data-testid="stMetric"] label,
[data-testid="stMetric"] div { color: white !important; }
[data-testid="stExpander"] summary { color: #87CEEB !important; font-weight: bold; }
@@ -83,6 +122,27 @@
    # MODIFIED: Also reset the slider tracker
    st.session_state.last_num_qubits = -1
    st.rerun()
# --- Sidebar Controls ---
st.sidebar.title("Circuit Controls")
num_qubits = st.sidebar.slider(...)
...

if st.sidebar.button("Clear and Reset Circuit", type="primary"):
    ...
    st.rerun()

# 🔽 PLACE NOISE CONTROLS HERE
st.sidebar.markdown("---")
st.sidebar.subheader("Quantum Noise")

enable_noise = st.sidebar.checkbox("Enable Noise", value=False)

with st.sidebar.expander("Noise Parameters"):
    depol_p = st.sidebar.slider("Depolarization", 0.0, 0.3, 0.0)
    decay_f = st.sidebar.slider("Amplitude Damping (T1)", 0.0, 0.3, 0.0)
    phase_g = st.sidebar.slider("Phase Damping (T2)", 0.0, 0.3, 0.0)
    ro_01 = st.sidebar.slider("|0⟩ → |1⟩ (Readout)", 0.0, 0.3, 0.0)
    ro_10 = st.sidebar.slider("|1⟩ → |0⟩ (Readout)", 0.0, 0.3, 0.0)

# --- Code Editor Input ---
st.subheader("</> Qiskit Code Editor")
@@ -199,7 +259,8 @@
                    st.info("No classical registers found. Adding measurements to all qubits.")
                    circuit_to_measure.measure_all(inplace=True)

                simulator = AerSimulator()
                noise_model = build_noise_model() if enable_noise else None
                simulator = AerSimulator(noise_model=noise_model)
                job = simulator.run(circuit_to_measure, shots=shots, memory=True)
                result = job.result()
                st.session_state.counts = result.get_counts(circuit_to_measure)
@@ -228,6 +289,12 @@
                st.write(counts)

        st.markdown("---")
        if enable_noise:
            st.info(
                "ℹ️ Bloch spheres show the ideal (noise-free) quantum state. "
                "Noise is applied during measurement simulation."
            )


        # --- Per-Qubit Bloch Sphere Visualizations ---
        if st.session_state.state_circuit.num_qubits <= 10:
@@ -250,3 +317,4 @@

    except Exception as e:
        st.error(f"Error during simulation or visualization: {e}")
