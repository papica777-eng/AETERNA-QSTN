# =============================================================================
# === AETERNA VHT NEUROLOGICAL ENGINE: CONNECTOME & PLV MATRIX (MOJO CORE) ===
# =============================================================================
# Complexity: O(C^2 * N) / Vectorized Phase Locking Value (PLV) Analysis
# Module: connectome_plv_engine.mojo
# =============================================================================

from math import sin, cos, atan2, sqrt, pi
from collections import List

struct ConnectivityPair:
    var channel_a: String
    var channel_b: String
    var plv_value: Float64

    fn __init__(out self, ch_a: String, ch_b: String, plv: Float64):
        self.channel_a = ch_a
        self.channel_b = ch_b
        self.plv_value = plv

    fn print_edge(self):
        print("Edge [", self.channel_a, " <-> ", self.channel_b, "] PLV:", self.plv_value)


struct ConnectivityMatrix:
    var channel_names: List[String]
    var matrix: List[List[Float64]]
    var channel_count: Int

    fn __init__(out self, names: List[String]):
        self.channel_names = names
        self.channel_count = len(names)
        self.matrix = List[List[Float64]]()
        for i in range(self.channel_count):
            var row = List[Float64]()
            for j in range(self.channel_count):
                if i == j:
                    row.append(1.0)
                else:
                    row.append(0.0)
            self.matrix.append(row)

    fn set_plv(mut self, i: Int, j: Int, val: Float64):
        if i < self.channel_count and j < self.channel_count:
            self.matrix[i][j] = val
            self.matrix[j][i] = val

    fn print_matrix(self):
        print("=== [AETERNA CONNECTOME PLV FUNCTIONAL MATRIX] ===")
        for i in range(self.channel_count):
            var row_str: String = self.channel_names[i] + "\t| "
            for j in range(self.channel_count):
                var val_str = String(self.matrix[i][j])
                row_str += val_str + "\t"
            print(row_str)
        print("==================================================")


fn calculate_instantaneous_phase(signal: List[Float64]) -> List[Float64]:
    """
    Approximates instantaneous phase via derivative zero-crossings and quadrature estimation.
    """
    var n = len(signal)
    var phases = List[Float64]()
    if n == 0:
        return phases

    for i in range(n):
        var next_idx = i + 1 if i + 1 < n else i
        var prev_idx = i - 1 if i > 0 else 0
        var derivative = (signal[next_idx] - signal[prev_idx]) / 2.0
        var phase = atan2(derivative, signal[i])
        phases.append(phase)

    return phases


fn compute_pairwise_plv(
    signal_a: List[Float64],
    signal_b: List[Float64]
) -> Float64:
    """
    Calculates Phase Locking Value (PLV):
    PLV = 1/N * | sum_{t=1}^N exp(i * (phase_a(t) - phase_b(t))) |
    Range: [0.0, 1.0] where 1.0 indicates perfect phase synchrony.
    """
    var n = min(len(signal_a), len(signal_b))
    if n == 0:
        return 0.0

    var phase_a = calculate_instantaneous_phase(signal_a)
    var phase_b = calculate_instantaneous_phase(signal_b)

    var sum_cos: Float64 = 0.0
    var sum_sin: Float64 = 0.0

    for t in range(n):
        var phase_diff = phase_a[t] - phase_b[t]
        sum_cos += cos(phase_diff)
        sum_sin += sin(phase_diff)

    var real_part = sum_cos / Float64(n)
    var imag_part = sum_sin / Float64(n)

    var plv = sqrt(real_part * real_part + imag_part * imag_part)
    return plv


fn main():
    print("Initializing AETERNA Connectome PLV Engine...")
    var channel_names = List[String]()
    channel_names.append("Fp1")
    channel_names.append("Fp2")
    channel_names.append("C3")
    channel_names.append("C4")
    channel_names.append("O1")

    var n_samples = 256
    var sig_fp1 = List[Float64]()
    var sig_fp2 = List[Float64]()
    var sig_c3 = List[Float64]()
    var sig_c4 = List[Float64]()
    var sig_o1 = List[Float64]()

    # Generate synthetic synchronized and independent rhythms
    for i in range(n_samples):
        var t = Float64(i) / 256.0
        var theta_master = sin(2.0 * pi * 6.0 * t)
        var alpha_occipital = sin(2.0 * pi * 10.0 * t)

        sig_fp1.append(theta_master + 0.1 * sin(2.0 * pi * 50.0 * t))
        sig_fp2.append(theta_master + 0.15 * cos(2.0 * pi * 50.0 * t)) # highly locked with Fp1
        sig_c3.append(0.5 * theta_master + 0.5 * sin(2.0 * pi * 20.0 * t))
        sig_c4.append(sin(2.0 * pi * 22.0 * t)) # independent
        sig_o1.append(alpha_occipital)

    var matrix = ConnectivityMatrix(channel_names)

    var signals = List[List[Float64]]()
    signals.append(sig_fp1)
    signals.append(sig_fp2)
    signals.append(sig_c3)
    signals.append(sig_c4)
    signals.append(sig_o1)

    for i in range(len(channel_names)):
        for j in range(i + 1, len(channel_names)):
            var plv = compute_pairwise_plv(signals[i], signals[j])
            matrix.set_plv(i, j, plv)

    matrix.print_matrix()
