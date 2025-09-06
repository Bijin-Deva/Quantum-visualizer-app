# app.py - Updated with Final System State display and custom background

import streamlit as st
import numpy as np
from qiskit import QuantumCircuit, qasm2
from qiskit.quantum_info import DensityMatrix, Statevector # Add Statevector import

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

# --- Custom Background Style ---
st.markdown("""
<style>
.stApp {
    background-image: linear-gradient(to bottom right, #000000, #0D224F);
    background-attachment: fixed;
    background-size: cover;
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

# --- Main Application Content ---
st.title("Quantum Circuit Simulator & Visualizer")
st.markdown("Write your own Qiskit code below to build a quantum circuit and visualize the results.")

# --- Sidebar Controls ---
st.sidebar.title("Circuit Controls")
num_qubits = st.sidebar.slider("Number of Qubits", min_value=1, max_value=5, value=2, key='num_qubits_slider')
st.sidebar.markdown("---")
if st.sidebar.button("Clear and Reset Circuit", type="primary"):
    st.session_state.circuit = None
    st.session_state.qasm_code = ""
    st.session_state.user_code = ""
    st.rerun()

# --- Code Editor Input ---
st.header("</> Qiskit Code Editor")
st.markdown("Define your circuit in the text area below. The circuit object **must** be named `qc`.")

default_code = (
    f"# Create a quantum circuit with {num_qubits} qubits\n"
    f"qc = QuantumCircuit({num_qubits})\n\n"
    "# Example: Create an entangled Bell state.\n"
    "# This state is pure, so you'll see the statevector below.\n"
    "qc.h(0)\n"
    "qc.cx(0, 1)\n\n"
    "# Try your own gates!\n"
    "# qc.x(0)\n"
    "# qc.ry(np.pi/2, 1)\n"
)

# Use session state to preserve code on reruns
if not st.session_state.user_code:
    st.session_state.user_code = default_code

user_code = st.text_area("Your Qiskit Code:", st.session_state.user_code, height=250, label_visibility="collapsed")

if st.button("Run Simulation", type="primary"):
    st.session_state.user_code = user_code # Save current code to state
    try:
        exec_globals = {
            "QuantumCircuit": QuantumCircuit,
            "np": np
        }
        exec(user_code, exec_globals)
        
        circuit = exec_globals.get("qc")

        if circuit and isinstance(circuit, QuantumCircuit):
            st.session_state.circuit = circuit
            st.session_state.qasm_code = qasm2.dumps(circuit)
            st.success("Circuit created successfully!")
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
    
    # --- Row 1: Diagram and QASM ---
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Circuit Diagram")
            try:
                fig_circuit = st.session_state.circuit.draw(output='mpl', style={'fontsize': 12})
                st.pyplot(fig_circuit)
            except Exception as e:
                st.error(f"Error drawing circuit: {e}")
                st.code(str(st.session_state.circuit))
                
        with col2:
            st.subheader("OpenQASM Code")
            st.code(st.session_state.qasm_code, language='qasm')

    st.markdown("---")

    try:
        # Calculate the full density matrix once for all subsequent calculations
        full_dm_obj = get_full_density_matrix_from_circuit(st.session_state.circuit)
        
        # --- NEW: Final System State Display ---
        st.subheader("Final System State")
        # Check purity to decide whether to show the statevector or density matrix
        full_purity = purity_from_rho(full_dm_obj.data)
        if np.isclose(full_purity, 1.0):
            st.markdown("The final system state is **pure**. Displaying the Statevector:")
            final_statevector = Statevector.from_instruction(st.session_state.circuit)
            st.code(str(final_statevector), language='text')
        else:
            st.markdown(f"The final system state is **mixed** (Purity = {full_purity:.4f}). Displaying the full Density Matrix:")
            st.code(str(full_dm_obj), language='text')

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
                    st.text("Reduced Density Matrix:")
                    st.dataframe(np.round(reduced_dm_data, 3))
    except Exception as e:
        st.error(f"Error during simulation or visualization: {e}")

