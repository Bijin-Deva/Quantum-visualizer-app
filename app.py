# app.py - New Graphical Interface Version

import streamlit as st
from quantum_utils import (
    create_circuit_from_gates,
    get_full_density_matrix_from_circuit,
    get_reduced_density_matrix,
    get_bloch_vector_from_rho,
    purity_from_rho,
    DensityMatrix
)
from bloch_plot import plot_bloch_sphere
from qiskit import QuantumCircuit, qasm2
import numpy as np

# Set the Streamlit page configuration
st.set_page_config(
    layout="wide", 
    page_title="Quantum State Visualizer"
)

# --- Session State Initialization ---
# Persist data across reruns
if 'circuit' not in st.session_state:
    st.session_state.circuit = None
if 'gate_list' not in st.session_state:
    st.session_state.gate_list = []
if 'qasm_code' not in st.session_state:
    st.session_state.qasm_code = ""

# --- Main Application Content ---
st.title("Quantum Circuit Simulator & Visualizer")
st.markdown("Build your quantum circuit using the controls below and see the individual qubit states on the Bloch sphere.")

# --- Sidebar Controls ---
num_qubits = st.sidebar.slider("Number of Qubits", min_value=1, max_value=5, value=2, key='num_qubits_slider')
st.sidebar.markdown("---")
if st.sidebar.button("Clear and Reset Circuit"):
    st.session_state.gate_list = []
    st.session_state.circuit = None
    st.session_state.qasm_code = ""
    st.rerun()

# --- Graphical Circuit Builder ---
st.header("Circuit Builder")

# Display the gates added so far
if st.session_state.gate_list:
    st.markdown("**Current Gates in Circuit:**")
    gate_display = " -> ".join([f"{g[0].upper()}{g[1:]}" for g in st.session_state.gate_list])
    st.info(gate_display)
else:
    st.info("Your circuit is currently empty. Add some gates!")

# Expander for adding new gates
with st.expander("Add a Gate", expanded=True):
    # Use columns for a clean layout
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col1:
        gate_type = st.selectbox(
            "Select Gate",
            ['Hadamard (h)', 'Pauli-X (x)', 'Pauli-Y (y)', 'Pauli-Z (z)', 'CNOT (cx)', 'CZ (cz)', 'RX Gate (rx)', 'RY Gate (ry)', 'RZ Gate (rz)'],
            key='gate_type'
        )
        gate_name = gate_type.split('(')[1][:-1] # Extracts 'h' from 'Hadamard (h)'

    qubit_options = list(range(num_qubits))
    
    with col2:
        target_qubit = st.selectbox("Target Qubit", qubit_options, key='target_qubit')

    # Logic for two-qubit gates and parameterized gates
    is_two_qubit = gate_name in ['cx', 'cz']
    is_parameterized = gate_name in ['rx', 'ry', 'rz']

    with col3:
        if is_two_qubit:
            control_qubit = st.selectbox(
                "Control Qubit", 
                [q for q in qubit_options if q != target_qubit], 
                key='control_qubit'
            )
        else:
            st.write("") # Placeholder for alignment

    with col4:
        if is_parameterized:
            angle_degrees = st.slider("Angle (θ) in Degrees", 0, 360, 90)
            angle_radians = np.deg2rad(angle_degrees)
        else:
            st.write("") # Placeholder

    # Button to add the selected gate to the list
    if st.button("Add Gate to Circuit"):
        if is_two_qubit:
            st.session_state.gate_list.append((gate_name, control_qubit, target_qubit))
        elif is_parameterized:
            st.session_state.gate_list.append((gate_name, target_qubit, angle_radians))
        else:
            st.session_state.gate_list.append((gate_name, target_qubit))
        st.rerun()

# Button to trigger the simulation
if st.button("Build and Run Simulation", type="primary"):
    if not st.session_state.gate_list:
        st.warning("Your circuit is empty. Please add at least one gate before running.")
    else:
        try:
            # Use the existing utility function to create the circuit from the gate list
            circuit = create_circuit_from_gates(num_qubits, st.session_state.gate_list)
            st.session_state.circuit = circuit
            
            # Generate QASM code
            # NEW, CORRECTED CODE
            st.session_state.qasm_code = qasm2.dumps(circuit)
            st.success("Circuit built and simulated successfully!")
            st.rerun() # Rerun to show the results below
        except Exception as e:
            st.error(f"Error building the circuit: {e}")
            st.session_state.circuit = None

# --- Circuit Visualization and Simulation Results ---
# This section only runs if a valid circuit is stored in session state
if st.session_state.circuit is not None:
    st.markdown("---")
    st.subheader("Generated Quantum Circuit")
    
    # Draw the circuit
    try:
        fig_circuit = st.session_state.circuit.draw(output='mpl', style={'fontsize': 10})
        st.pyplot(fig_circuit)
    except Exception as e:
        st.error(f"Error drawing circuit: {e}")
        st.code(str(st.session_state.circuit))

    st.markdown("And its Qiskit OpenQASM code:")
    st.code(st.session_state.qasm_code, language='qasm')

    st.subheader("Bloch Sphere Visualizations")
    try:
        full_dm_obj = get_full_density_matrix_from_circuit(st.session_state.circuit)
        
        cols = st.columns(num_qubits)
        for i in range(num_qubits):
            with cols[i]:
                st.markdown(f"#### Qubit {i}")
                reduced_dm_data = get_reduced_density_matrix(full_dm_obj, num_qubits, i)
                bx, by, bz = get_bloch_vector_from_rho(reduced_dm_data)
                purity = purity_from_rho(reduced_dm_data)

                st.plotly_chart(plot_bloch_sphere(bx, by, bz, f"Qubit {i} State"), use_container_width=True)
                st.metric(label=f"Purity", value=f"{purity:.4f}")
                with st.expander(f"Details for Qubit {i}"):
                    st.markdown(f"**Bloch Vector:** ({bx:.3f}, {by:.3f}, {bz:.3f})")
                    st.markdown(f"**Reduced Density Matrix:**")
                    st.write(reduced_dm_data)

    except Exception as e:

        st.error(f"Error during simulation or visualization: {e}")
