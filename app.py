# app.py - Final fix for removing the top white bar, styling expanders, and repositioning output

import streamlit as st
import numpy as np
from qiskit import QuantumCircuit, qasm2
from qiskit.quantum_info import DensityMatrix, Statevector

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
    background-color: #0A193D; /* A solid dark blue that matches the theme */
}

/* Sidebar text color fix */
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: white !important;
}

/* Purity metric (st.metric) styling fix */
[data-testid="stMetric"] label,
[data-testid="stMetric"] div {
    color: white !important;
}

/* MODIFIED: Custom styling for the details expander */
[data-testid="stExpander"] summary {
    color: #87CEEB !important; /* A light, techy blue */
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

# --- Main Application Content ---
st.title("⚛️ Quantum Circuit Simulator & Visualizer")
st.markdown("Your sandbox for quantum computation. Write Qiskit code, run simulations, and visualize results instantly.")
st.markdown("---")

# --- Sidebar Controls (Restored) ---
st.sidebar.title("Circuit Controls")
num_qubits = st.sidebar.slider("Number of Qubits", min_value=1, max_value=5, value=2, key='num_qubits_slider', help="Adjust the number of qubits for your circuit.")
st.sidebar.markdown("---")
if st.sidebar.button("Clear and Reset Circuit", type="primary"):
    st.session_state.circuit = None
    st.session_state.qasm_code = ""
    st.session_state.user_code = ""
    st.rerun()

# --- Code Editor Input ---
st.subheader("</> Qiskit Code Editor")
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
    
    try:
        # Calculate the full density matrix once for all subsequent calculations
        full_dm_obj = get_full_density_matrix_from_circuit(st.session_state.circuit)
        
        # --- Row 1: Diagram, QASM, and Final State ---
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
                
                # MODIFIED: Final System State Display is now in the second column
                st.subheader("Final System State")
                full_purity = purity_from_rho(full_dm_obj.data)
                if np.isclose(full_purity, 1.0):
                    st.markdown("The system is in a **pure state**.")
                    final_statevector = Statevector.from_instruction(st.session_state.circuit)
                    st.code(str(final_statevector), language='text')
                else:
                    st.markdown(f"The system is in a **mixed state** (Purity = {full_purity:.4f}).")
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
                
                # This expander will now be styled due to the CSS added above
                with st.expander(f"Details for Qubit {i}"):
                    st.markdown(f"**Bloch Vector:** `({bx:.3f}, {by:.3f}, {bz:.3f})`")
                    st.markdown("Reduced Density Matrix:")
                    st.dataframe(np.round(reduced_dm_data, 3))
    except Exception as e:
        st.error(f"Error during simulation or visualization: {e}")
