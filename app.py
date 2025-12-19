
# app.py - Fixed default code generation to be dynamic and robust.

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
# NOTE: You will need to have your 'quantum_utils.py' and 'bloch_plot.py' files
# in the same directory for these imports to work.
from quantum_utils import (
    get_full_density_matrix_from_circuit,
    get_reduced_density_matrix,
    get_bloch_vector_from_rho,
    purity_from_rho,
)
from bloch_plot import plot_bloch_sphere
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
# --- Page and Session State Setup ---
st.set_page_config(
    layout="wide",
    page_title="Quantum State Visualizer"
)

# --- Custom Styling for Main App and Sidebar ---
st.markdown("""
<style>
/* Main app background */
.stApp {
    background-color: #EAF4FF; /* Light blue */
}

/* Header */
[data-testid="stHeader"] {
    background-color: transparent;
}

/* Main text */
[data-testid="stAppViewContainer"] {
    color: #000000;
}

[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] .stMarkdown p {
    color: #000000 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #D6EBFF; /* Slightly darker light blue */
}

[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #000000 !important;
}

/* Metrics */
[data-testid="stMetric"] label,
[data-testid="stMetric"] div {
    color: #000000 !important;
}

/* Expander headers */
[data-testid="stExpander"] summary {
    color: #003366 !important;
    font-weight: bold;
}

/* Code editor */
textarea {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #A0C4FF !important;
}
</style>
""", unsafe_allow_html=True)


# Initialize session state variables
if 'circuit' not in st.session_state:
    st.session_state.circuit = None
if 'state_circuit' not in st.session_state:
    st.session_state.state_circuit = None
if 'qasm_code' not in st.session_state:
    st.session_state.qasm_code = ""
if 'user_code' not in st.session_state:
    st.session_state.user_code = ""
if 'counts' not in st.session_state:
    st.session_state.counts = None
# MODIFIED: Add a new state to track the slider value to force code updates
if 'last_num_qubits' not in st.session_state:
    st.session_state.last_num_qubits = -1

# --- Main Application Content ---
st.title("⚛️ Quantum Circuit Simulator & Visualizer")
st.markdown("Your sandbox for quantum computation. Write Qiskit code, run simulations, and visualize results instantly.")
st.markdown("---")

# --- Sidebar Controls ---
st.sidebar.title("Circuit Controls")
num_qubits = st.sidebar.slider("Number of Qubits", min_value=1, max_value=5, value=2, key='num_qubits_slider', help="Adjust the number of qubits for your circuit.")
st.sidebar.markdown("---")
if st.sidebar.button("Clear and Reset Circuit", type="primary"):
    st.session_state.circuit = None
    st.session_state.state_circuit = None
    st.session_state.qasm_code = ""
    st.session_state.user_code = ""
    st.session_state.counts = None
    # MODIFIED: Also reset the slider tracker
    st.session_state.last_num_qubits = -1
    st.rerun()
# 🔽 STEP 3: Noise Controls (PLACE HERE)
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
st.markdown("Define your circuit in the text area below. The circuit object **must** be named `qc`.")

# ######################################################################
# # --- MODIFIED: Default code generation is now dynamic and robust ---
# ######################################################################

# Base part of the code
qc_init_code = f"# Create a quantum circuit with {num_qubits} qubits and classical bits\nqc = QuantumCircuit({num_qubits}, {num_qubits})\n"

# Example part of the code, which changes based on qubit count
if num_qubits >= 2:
    example_code = (
        "\n# Example: Create a Bell state |Φ+> and measure it\n"
        "qc.h(0)\n"
        "qc.cx(0, 1)\n"
        "qc.barrier()\n"
        "qc.measure([0, 1], [0, 1])\n"
    )
else: # num_qubits == 1
    example_code = (
        "\n# Example: Create a superposition on a single qubit\n"
        "qc.h(0)\n"
        "qc.barrier()\n"
        "qc.measure(0, 0)\n"
    )

default_code = qc_init_code + example_code

# If the slider has changed, or if the code is blank, update the text area with the new default
if st.session_state.last_num_qubits != num_qubits or not st.session_state.user_code:
    st.session_state.user_code = default_code
    st.session_state.last_num_qubits = num_qubits

user_code = st.text_area("Your Qiskit Code:", st.session_state.user_code, height=250, label_visibility="collapsed")

# ######################################################################
# # --- END OF MODIFICATION ---
# ######################################################################


if st.button("Run Simulation", type="primary"):
    st.session_state.user_code = user_code
    st.session_state.counts = None
    try:
        exec_globals = {"QuantumCircuit": QuantumCircuit, "ClassicalRegister": ClassicalRegister, "np": np}
        exec(user_code, exec_globals)
        circuit = exec_globals.get("qc")

        if circuit and isinstance(circuit, QuantumCircuit):
            st.session_state.circuit = circuit
            st.session_state.qasm_code = qasm2.dumps(circuit)
            
            state_circuit = circuit.copy()
            state_circuit.remove_final_measurements(inplace=True)
            st.session_state.state_circuit = state_circuit
            
            st.success("Circuit created and state simulated successfully!")
            st.rerun()
        else:
            st.error("Execution succeeded, but a QuantumCircuit object named 'qc' was not found.")
    except Exception as e:
        st.error(f"Error in your code: {e}")
        st.session_state.circuit = None
        st.session_state.state_circuit = None


# --- Visualization Section ---
if st.session_state.circuit is not None and st.session_state.state_circuit is not None:
    st.markdown("---")
    st.header("Simulation Results")
    
    try:
        # Prevent running state analysis on very large systems to avoid crashing Streamlit
        if st.session_state.state_circuit.num_qubits > 10:
             st.warning("State vector and density matrix analysis is disabled for circuits with more than 10 qubits to ensure performance.")
        else:
            full_dm_obj = get_full_density_matrix_from_circuit(st.session_state.state_circuit)
        
        # Row 1: Diagram, QASM, and State
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Circuit Diagram")
                fig_circuit = st.session_state.circuit.draw(output='mpl', style={'fontsize': 12})
                st.pyplot(fig_circuit)
            with col2:
                st.subheader("OpenQASM Code")
                st.code(st.session_state.qasm_code, language='qasm')
                if st.session_state.state_circuit.num_qubits <= 10:
                    st.subheader("Final System State (Before Measurement)")
                    full_purity = purity_from_rho(full_dm_obj.data)
                    if np.isclose(full_purity, 1.0):
                        st.markdown("The system is in a **pure state**.")
                        final_statevector = Statevector.from_instruction(st.session_state.state_circuit)
                        st.code(str(final_statevector), language='text')
                    else:
                        st.markdown(f"The system is in a **mixed state** (Purity = {full_purity:.4f}).")
                        st.code(str(full_dm_obj), language='text')

        st.markdown("---")

        # --- Measurement Simulation Section ---
        st.subheader("🔬 Classical Measurement Outcome")
        st.markdown("Simulate running the circuit on an ideal quantum computer.")
        
        shots = 1024
        if st.button(f"Measure and Run ({shots} Shots)", type="primary"):
            with st.spinner("Simulating measurements..."):
                circuit_to_measure = st.session_state.circuit.copy()
                if not circuit_to_measure.cregs:
                    st.info("No classical registers found. Adding measurements to all qubits.")
                    circuit_to_measure.measure_all(inplace=True)

                noise_model = None
                if enable_noise:
                    noise_model = build_noise_model(
                    depol_p, decay_f, phase_g, ro_01, ro_10
                    )

                simulator = AerSimulator(noise_model=noise_model)
                job = simulator.run(circuit_to_measure, shots=shots, memory=True)

                result = job.result()
                st.session_state.counts = result.get_counts(circuit_to_measure)
                st.rerun()

        if st.session_state.counts:
            st.markdown(f"**Results from {shots} shots**")
            counts = st.session_state.counts
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=list(counts.keys()),
                y=list(counts.values()),
                marker_color='#d65f5f'
            ))
            fig.update_layout(
                xaxis_title='Measured State', yaxis_title='Counts',
                template='plotly_dark', bargap=0.5
            )
            st.plotly_chart(fig, use_container_width=True)

            most_probable_outcome = max(counts, key=counts.get)
            st.metric(label="Most Probable Outcome", value=most_probable_outcome)
            
            with st.expander("Show Raw Counts"):
                st.write(counts)
        
        st.markdown("---")
        if enable_noise:
            st.info(
                "ℹ️ Bloch spheres show the ideal (noise-free) quantum state. "
                "Noise is applied only during measurement simulation."
            )
        # --- Per-Qubit Bloch Sphere Visualizations ---
        if st.session_state.state_circuit.num_qubits <= 10:
            st.subheader("Per-Qubit Bloch Sphere Visualizations (State Before Measurement)")
            display_qubits = st.session_state.state_circuit.num_qubits
            cols = st.columns(display_qubits)
            for i in range(display_qubits):
                with cols[i]:
                    reduced_dm_data = get_reduced_density_matrix(full_dm_obj, display_qubits, i)
                    bx, by, bz = get_bloch_vector_from_rho(reduced_dm_data)
                    purity = purity_from_rho(reduced_dm_data)

                    st.plotly_chart(plot_bloch_sphere(bx, by, bz, f"Qubit {i}"), use_container_width=True)
                    st.metric(label=f"Purity (Qubit {i})", value=f"{purity:.4f}")
                    
                    with st.expander(f"Details for Qubit {i}"):
                        st.markdown(f"**Bloch Vector:** `({bx:.3f}, {by:.3f}, {bz:.3f})`")
                        st.markdown("Reduced Density Matrix:")
                        st.dataframe(np.round(reduced_dm_data, 3))

    except Exception as e:
        st.error(f"Error during simulation or visualization: {e}")



