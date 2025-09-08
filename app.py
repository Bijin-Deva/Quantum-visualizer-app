# app.py - Styled the measurement button to match the theme

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from qiskit import QuantumCircuit, qasm2, ClassicalRegister
from qiskit.quantum_info import DensityMatrix, Statevector
from qiskit_aer import AerSimulator

from quantum_utils import (
    get_full_density_matrix_from_circuit,
    get_reduced_density_matrix,
    get_bloch_vector_from_rho,
    purity_from_rho,
)
from bloch_plot import plot_bloch_sphere

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
    background-image: linear-gradient(to bottom right, #000000, #0D224F);
    background-attachment: fixed;
    background-size: cover;
}

/* This rule removes the white header bar at the top */
[data-testid="stHeader"] {
    background-color: transparent;
}

/* Main content text color fix */
[data-testid="stAppViewContainer"] {
    color: white;
}
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] .stMarkdown p {
    color: white !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #0A193D;
}

/* Sidebar text color fix */
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: white !important;
}

/* Metric and Expander styling */
[data-testid="stMetric"] label,
[data-testid="stMetric"] div {
    color: white !important;
}
[data-testid="stExpander"] summary {
    color: #87CEEB !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'circuit' not in st.session_state:
    st.session_state.circuit = None
if 'qasm_code' not in st.session_state:
    st.session_state.qasm_code = ""
if 'user_code' not in st.session_state:
    st.session_state.user_code = ""
if 'counts' not in st.session_state:
    st.session_state.counts = None

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
    st.session_state.qasm_code = ""
    st.session_state.user_code = ""
    st.session_state.counts = None
    st.rerun()

# --- Code Editor Input ---
st.subheader("</> Qiskit Code Editor")
st.markdown("Define your circuit in the text area below. The circuit object **must** be named `qc`.")

default_code = (
    f"# Create a quantum circuit with {num_qubits} qubits\n"
    f"qc = QuantumCircuit({num_qubits})\n\n"
    "# Example: Create a Bell state |Φ+>\n"
    "qc.h(0)\n"
    "qc.cx(0, 1)\n"
)

if not st.session_state.user_code:
    st.session_state.user_code = default_code

user_code = st.text_area("Your Qiskit Code:", st.session_state.user_code, height=250, label_visibility="collapsed")

if st.button("Run Simulation"): # Kept this as a secondary button
    st.session_state.user_code = user_code
    st.session_state.counts = None
    try:
        exec_globals = {"QuantumCircuit": QuantumCircuit, "np": np}
        exec(user_code, exec_globals)
        circuit = exec_globals.get("qc")

        if circuit and isinstance(circuit, QuantumCircuit):
            st.session_state.circuit = circuit
            st.session_state.qasm_code = qasm2.dumps(circuit)
            st.success("Circuit created and state simulated successfully!")
            st.rerun()
        else:
            st.error("Execution succeeded, but a QuantumCircuit object named 'qc' was not found.")
    except Exception as e:
        st.error(f"Error in your code: {e}")
        st.session_state.circuit = None

# --- Visualization Section ---
if st.session_state.circuit is not None:
    st.markdown("---")
    st.header("Simulation Results")
    
    try:
        full_dm_obj = get_full_density_matrix_from_circuit(st.session_state.circuit)
        
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
                st.subheader("Final System State (Before Measurement)")
                full_purity = purity_from_rho(full_dm_obj.data)
                if np.isclose(full_purity, 1.0):
                    st.markdown("The system is in a **pure state**.")
                    final_statevector = Statevector.from_instruction(st.session_state.circuit)
                    st.code(str(final_statevector), language='text')
                else:
                    st.markdown(f"The system is in a **mixed state** (Purity = {full_purity:.4f}).")
                    st.code(str(full_dm_obj), language='text')

        st.markdown("---")

        # --- Measurement Simulation Section ---
        st.subheader("🔬 Classical Measurement Outcome")
        st.markdown("Simulate running the circuit on an ideal quantum computer.")
        
        shots = 1024
        # MODIFIED: Changed the button type to "primary" for better styling
        if st.button(f"Measure All Qubits ({shots} Shots)", type="primary"):
            with st.spinner("Simulating measurements..."):
                circuit_to_measure = st.session_state.circuit.copy()
                if not circuit_to_measure.cregs:
                    circuit_to_measure.measure_all(inplace=True)

                simulator = AerSimulator()
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
                xaxis_title='Measured State',
                yaxis_title='Counts',
                template='plotly_dark',
                bargap=0.5
            )
            st.plotly_chart(fig, use_container_width=True)

            most_probable_outcome = max(counts, key=counts.get)
            st.metric(label="Most Probable Outcome", value=most_probable_outcome)
            
            with st.expander("Show Raw Counts"):
                st.write(counts)
        
        st.markdown("---")

        # --- Per-Qubit Bloch Sphere Visualizations ---
        st.subheader("Per-Qubit Bloch Sphere Visualizations")
        display_qubits = st.session_state.circuit.num_qubits
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
