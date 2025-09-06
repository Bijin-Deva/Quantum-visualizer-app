# quantum_utils.py - Corrected code

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace

def get_full_density_matrix_from_circuit(circuit: QuantumCircuit) -> DensityMatrix:
    """
    Calculates the full density matrix for a given quantum circuit.

    Args:
        circuit: The Qiskit QuantumCircuit object.

    Returns:
        A DensityMatrix object representing the state of the system.
    """
    state_vector = Statevector.from_instruction(circuit)
    density_matrix = DensityMatrix(state_vector)
    return density_matrix

def get_reduced_density_matrix(full_dm: DensityMatrix, num_qubits: int, target_qubit: int) -> np.ndarray:
    """
    Performs partial tracing to get the reduced density matrix for a single qubit.

    Args:
        full_dm: The full DensityMatrix object for the system.
        num_qubits: The total number of qubits in the system.
        target_qubit: The index of the qubit to get the reduced density matrix for.

    Returns:
        A 2x2 numpy array representing the reduced density matrix.
    """
    if not isinstance(full_dm, DensityMatrix):
        # Handle cases where the input is not a Qiskit DensityMatrix object
        full_dm = DensityMatrix(full_dm)

    traced_out_qubits = [i for i in range(num_qubits) if i != target_qubit]
    
    # Corrected line: Use the module-level partial_trace function
    reduced_dm = partial_trace(full_dm, traced_out_qubits)
    
    return reduced_dm.data

def get_bloch_vector_from_rho(rho: np.ndarray) -> tuple:
    """
    Calculates the Bloch vector (x, y, z) from a 2x2 density matrix.

    Args:
        rho: A 2x2 numpy array representing the density matrix.

    Returns:
        A tuple (x, y, z) representing the Bloch vector coordinates.
    """
    # Pauli matrices
    pauli_x = np.array([[0, 1], [1, 0]])
    pauli_y = np.array([[0, -1j], [1j, 0]])
    pauli_z = np.array([[1, 0], [0, -1]])

    # Calculate Bloch vector components
    bx = np.real(np.trace(np.dot(pauli_x, rho)))
    by = np.real(np.trace(np.dot(pauli_y, rho)))
    bz = np.real(np.trace(np.dot(pauli_z, rho)))

    return (bx, by, bz)

def purity_from_rho(rho: np.ndarray) -> float:
    """
    Calculates the purity of a quantum state from its density matrix.
    Purity is given by Tr(rho^2).

    Args:
        rho: A 2x2 numpy array representing the density matrix.

    Returns:
        A float representing the purity of the state.
    """
    return np.real(np.trace(np.dot(rho, rho)))

def create_circuit_from_gates(num_qubits: int, gates: list) -> QuantumCircuit:
    """
    Creates a Qiskit QuantumCircuit from a list of gate tuples.

    Args:
        num_qubits: The total number of qubits in the circuit.
        gates: A list of tuples, where each tuple defines a gate and its targets.
               e.g., [('h', 0), ('cx', 0, 1)]

    Returns:
        A Qiskit QuantumCircuit object.
    """
    qc = QuantumCircuit(num_qubits)
    for gate in gates:
        gate_name = gate[0]
        if gate_name == 'h':
            qc.h(gate[1])
        elif gate_name == 'x':
            qc.x(gate[1])
        elif gate_name == 'y':
            qc.y(gate[1])
        elif gate_name == 'z':
            qc.z(gate[1])
        elif gate_name == 'rx':
            qc.rx(gate[2], gate[1])
        elif gate_name == 'ry':
            qc.ry(gate[2], gate[1])
        elif gate_name == 'rz':
            qc.rz(gate[2], gate[1])
        elif gate_name == 'cx':
            qc.cx(gate[1], gate[2])
        elif gate_name == 'cz':
            qc.cz(gate[1], gate[2])
    return qc