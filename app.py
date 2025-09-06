# app.py - Hybrid version with both Graphical and Code-based inputs

import streamlit as st
import numpy as np
from qiskit import QuantumCircuit, qasm2
from qiskit.quantum_info import DensityMatrix

from quantum_utils import (
    create_circuit_from_gates,
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

# Initialize session state variables to persist data across reruns
if 'circuit' not in st.session_state:
    st.session_state.circuit = None
if 'gate_list' not in st.session_state:
    st.session_state.gate_list = []
if 'qasm_code' not in st.session_state:
    st.session_state.qasm_code = ""
if 'user_code' not in st.session_state:
    st.session_state.user_code = ""

# --- Main Application Content ---
st.title("Quantum Circuit Simulator & Visualizer")
st.markdown("Build your quantum circuit using the graphical builder or write your own Qiskit code.")

# --- Sidebar Controls ---
st.sidebar.title("Circuit Controls")
num_qubits = st.sidebar.slider("Number of Qubits", min_value=1, max_value=5, value=2, key='num_qubits_slider')
st.sidebar.markdown("---")
if st.sidebar.button("Clear and Reset Circuit", type="primary"):
    st.session_state.gate_list = []
    st.session_state.circuit = None
    st.session_state.qasm_code = ""
    st.session_state.user_code = ""
    st.rerun()

# --- Input Tabs ---
st.header("Circuit Input Method")
tab1, tab2 = st.tabs(["**</> Code Editor**", "**✨ Graphical Builder**"])

# --- Tab 1: Code Editor ---
with tab1:
    st.markdown("Enter your Qiskit circuit code directly. The circuit object **must** be named `qc`.")
    default_code = (
        f"# Create a quantum circuit with {num_qubits} qubits\n"
        f"qc = QuantumCircuit({num_qubits})\n\n"
        "# Example: Create an entangled Bell state\n"
        "qc.h(0)\n"
        "qc.cx(0, 1)\n\n"
        "# Try your own gates!\n"
        "# qc.x(0)\n"
    )
    
    # Use session state to preserve code on reruns
    if not st.session_state.user_code:
        st.session_state.user_code = default_code

    user_code = st.text_area("Qiskit Code:", st.session_state.user_code, height=250)

    if st.button("Run Code Simulation"):
        st.session_state.user_code = user_code # Save current code
        try:
            # Prepare a safe execution environment
            exec_globals = {
                "QuantumCircuit": QuantumCircuit,
                "np": np
            }
            # Execute the user's code
            exec(user_code, exec_globals)
            
            # Retrieve the circuit object, which must be named 'qc'
            circuit = exec_globals.get("qc")

            if circuit and isinstance(circuit, QuantumCircuit):
                st.session_state.circuit = circuit
                # Use the modern qasm2.dumps method
                st.session_state.qasm_code = qasm2.dumps(circuit)
                # Clear the graphical gate list since code takes precedence
                st.session_state.gate_list = []
                st.success("Circuit created successfully from code!")
                st.rerun()
            else:
                st.error("Execution succeeded, but a QuantumCircuit object named 'qc' was not found.")

        except Exception as e:
            st.error(f"Error in your code: {e}")
            st.session_state.circuit = None

# --- Tab 2: Graphical Builder ---
with tab2:
    st.markdown("Add gates to your circuit one by one using the controls below.")
    
    # Display the gates added so far
    if st.session_state.gate_list:
        st.markdown("**Current Gates in Circuit:**")
        gate_display = " ➔ ".join([f"{g[0].upper()}{g[1:]}" for g in st.session_state.gate_list])
        st.info(gate_display)
    else:
        st.warning("Your circuit is empty. Add some gates!")

    with st.form("gate_form", clear_on_submit=True):
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 2, 1])
        with col1:
            gate_type = st.selectbox("Gate", ['Hadamard (h)', 'Pauli-X (x)', 'CNOT (cx)', 'Pauli-Y (y)', 'Pauli-Z (z)'], key='gate_type')
            gate_name = gate_type.split('(')[1][:-1]
        with col2:
            target_qubit = st.selectbox("Target", list(range(num_qubits)), key='target_qubit')
        with col3:
            control_qubit = st.selectbox("Control", list(range(num_qubits)), key='control_qubit', disabled=(gate_name not in ['cx', 'cz']))
        
        submitted = st.form_submit_button("Add Gate")
        if submitted:
            if gate_name in ['cx', 'cz'] and target_qubit == control_qubit:
                st.warning("Target and Control qubits cannot be the same.")
            else:
                if gate_name in ['cx', 'cz']:
                    st.session_state.gate_list.append((gate_name, control_qubit, target_qubit))
                else:
                    st.session_state.gate_list.append((gate_name, target_qubit))
                st.rerun()

    if st.button("Build and Run Graphical Circuit"):
        if not st.session_state.gate_list:
            st.warning("Please add at least one gate before running.")
        else:
            try:
                circuit = create_circuit_from_gates(num_qubits, st.session_state.gate_list)
                st.session_state.circuit = circuit
                st.session_state.qasm_code = qasm2.dumps(circuit)
                st.session_state.user_code = "" # Clear code input
                st.success("Circuit built and simulated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error building the circuit: {e}")
                st.session_state.circuit = None

# --- Common Visualization Section ---
# This section runs if a valid circuit exists in the session state,
# regardless of how it was created.
if st.session_state.circuit is not None:
    st.markdown("---")
    st.header("Simulation Results")
    
    # --- Circuit Diagram and QASM ---
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

    # --- Bloch Sphere Visualizations ---
    st.subheader("Bloch Sphere Visualizations")
    try:
        full_dm_obj = get_full_density_matrix_from_circuit(st.session_state.circuit)
        
        # Determine number of columns for display
        display_qubits = st.session_state.circuit.num_qubits
        cols = st.columns(display_qubits)

        for i in range(display_qubits):
            with cols[i]:
                st.markdown(f"#### Qubit {i}")
                reduced_dm_data = get_reduced_density_matrix(full_dm_obj, display_qubits, i)
                bx, by, bz = get_bloch_vector_from_rho(reduced_dm_data)
                purity = purity_from_rho(reduced_dm_data)

                st.plotly_chart(plot_bloch_sphere(bx, by, bz, f"Qubit {i}"), use_container_width=True)
                st.metric(label=f"Purity", value=f"{purity:.4f}")
                with st.expander(f"Details for Qubit {i}"):
                    st.markdown(f"**Bloch Vector:** `({bx:.3f}, {by:.3f}, {bz:.3f})`")
                    st.text("Reduced Density Matrix:")
                    st.dataframe(np.round(reduced_dm_data, 3))
    except Exception as e:
        st.error(f"Error during simulation or visualization: {e}")
