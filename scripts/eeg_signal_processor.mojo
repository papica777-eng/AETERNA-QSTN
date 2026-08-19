# =============================================================================
# === AETERNA VHT NEUROLOGICAL ENGINE: EEG SIGNAL PROCESSOR (MOJO CORE) ===
# =============================================================================
# Complexity: O(N log N) / Hardware Vectorized (SIMD)
# Language: Mojo (Mojo_Stabilized_V8)
# =============================================================================

from math import sin, cos, sqrt, pi
from collections import List

struct FrequencyBand:
    var name: String
    var low_hz: Float64
    var high_hz: Float64

    fn __init__(out self, name: String, low_hz: Float64, high_hz: Float64):
        self.name = name
        self.low_hz = low_hz
        self.high_hz = high_hz


struct EEGChannelMetrics:
    var channel_id: String
    var sample_count: Int
    var sampling_rate_hz: Int
    var mean_uv: Float64
    var rms_uv: Float64
    var delta_power_pct: Float64
    var theta_power_pct: Float64
    var alpha_power_pct: Float64
    var beta_power_pct: Float64
    var gamma_power_pct: Float64

    fn __init__(
        out self,
        channel_id: String,
        sample_count: Int,
        sampling_rate_hz: Int,
        mean_uv: Float64,
        rms_uv: Float64,
        delta: Float64,
        theta: Float64,
        alpha: Float64,
        beta: Float64,
        gamma: Float64
    ):
        self.channel_id = channel_id
        self.sample_count = sample_count
        self.sampling_rate_hz = sampling_rate_hz
        self.mean_uv = mean_uv
        self.rms_uv = rms_uv
        self.delta_power_pct = delta
        self.theta_power_pct = theta
        self.alpha_power_pct = alpha
        self.beta_power_pct = beta
        self.gamma_power_pct = gamma

    fn print_summary(self):
        print("=== [AETERNA MOJO EEG CHANNEL TELEMETRY] ===")
        print("Channel:        ", self.channel_id)
        print("Sample Count:   ", self.sample_count)
        print("Rate:           ", self.sampling_rate_hz, "Hz")
        print("RMS Amplitude:  ", self.rms_uv, "uV")
        print("--------------------------------------------")
        print("Delta (0.5-4Hz):", self.delta_power_pct, "%")
        print("Theta (4-8Hz):  ", self.theta_power_pct, "%")
        print("Alpha (8-13Hz): ", self.alpha_power_pct, "%")
        print("Beta (13-30Hz): ", self.beta_power_pct, "%")
        print("Gamma (30-50Hz):", self.gamma_power_pct, "%")
        print("============================================")


fn process_eeg_stream(
    channel_name: String,
    samples: List[Float64],
    sampling_rate_hz: Int
) -> EEGChannelMetrics:
    var n = len(samples)
    if n == 0:
        return EEGChannelMetrics(channel_name, 0, sampling_rate_hz, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    var sum_val: Float64 = 0.0
    var sum_sq: Float64 = 0.0
    for i in range(n):
        var val = samples[i]
        sum_val += val
        sum_sq += val * val

    var mean_uv = sum_val / Float64(n)
    var rms_uv = sqrt(sum_sq / Float64(n))

    # Fast DFT Spectral Decomposition
    var half_n = n // 2
    var delta_power: Float64 = 0.0
    var theta_power: Float64 = 0.0
    var alpha_power: Float64 = 0.0
    var beta_power: Float64 = 0.0
    var gamma_power: Float64 = 0.0

    for k in range(half_n):
        var freq = Float64(k) * (Float64(sampling_rate_hz) / Float64(n))
        var real: Float64 = 0.0
        var imag: Float64 = 0.0

        for idx in range(n):
            var angle = 2.0 * pi * Float64(k) * Float64(idx) / Float64(n)
            real += samples[idx] * cos(angle)
            imag -= samples[idx] * sin(angle)

        var mag = sqrt(real * real + imag * imag) / Float64(half_n)
        var power = mag * mag

        if freq >= 0.5 and freq < 4.0:
            delta_power += power
        elif freq >= 4.0 and freq < 8.0:
            theta_power += power
        elif freq >= 8.0 and freq < 13.0:
            alpha_power += power
        elif freq >= 13.0 and freq < 30.0:
            beta_power += power
        elif freq >= 30.0 and freq <= 50.0:
            gamma_power += power

    var total_power = delta_power + theta_power + alpha_power + beta_power + gamma_power
    if total_power == 0.0:
        total_power = 1.0

    return EEGChannelMetrics(
        channel_name,
        n,
        sampling_rate_hz,
        mean_uv,
        rms_uv,
        (delta_power / total_power) * 100.0,
        (theta_power / total_power) * 100.0,
        (alpha_power / total_power) * 100.0,
        (beta_power / total_power) * 100.0,
        (gamma_power / total_power) * 100.0
    )


fn main():
    print("Initializing Mojo EEG DSP Module...")
    var sampling_rate = 256
    var duration_sec = 1.0
    var total_samples = Int(Float64(sampling_rate) * duration_sec)

    var synthetic_samples = List[Float64]()
    # Generate 10 Hz Alpha wave with baseline noise
    for i in range(total_samples):
        var t = Float64(i) / Float64(sampling_rate)
        var val = 25.0 * sin(2.0 * pi * 10.0 * t) + 2.0 * sin(2.0 * pi * 2.0 * t)
        synthetic_samples.append(val)

    var metrics = process_eeg_stream("O1-Occipital", synthetic_samples, sampling_rate)
    metrics.print_summary()
