# =============================================================================
# === AETERNA VHT NEUROLOGICAL ENGINE: ARTIFACT FILTER & ERP DETECTOR (MOJO) ===
# =============================================================================
# Complexity: O(N) / Z-Score Adaptive Thresholding & Event-Related Potentials
# Module: neuro_artifact_erp_filter.mojo
# =============================================================================

from math import sqrt
from collections import List

struct ERPDetectionResult:
    var peak_latency_ms: Float64
    var peak_amplitude_uv: Float64
    var p300_detected: Bool
    var confidence_score: Float64

    fn __init__(
        out self,
        latency: Float64,
        amplitude: Float64,
        detected: Bool,
        confidence: Float64
    ):
        self.peak_latency_ms = latency
        self.peak_amplitude_uv = amplitude
        self.p300_detected = detected
        self.confidence_score = confidence

    fn print_report(self):
        print("=== [AETERNA ERP P300 DETECTION TELEMETRY] ===")
        print("P300 Detected:     ", self.p300_detected)
        print("Peak Latency (ms): ", self.peak_latency_ms)
        print("Peak Amplitude (uV):", self.peak_amplitude_uv)
        print("Confidence Score:  ", self.confidence_score)
        print("==============================================")


struct ArtifactFilterStats:
    var original_sample_count: Int
    var rejected_artifact_count: Int
    var clean_ratio_pct: Float64

    fn __init__(out self, orig: Int, rejected: Int):
        self.original_sample_count = orig
        self.rejected_artifact_count = rejected
        if orig > 0:
            self.clean_ratio_pct = (Float64(orig - rejected) / Float64(orig)) * 100.0
        else:
            self.clean_ratio_pct = 0.0

    fn print_summary(self):
        print("=== [AETERNA ARTIFACT SUPPRESSION AUDIT] ===")
        print("Total Samples:   ", self.original_sample_count)
        print("Artifact Samples:", self.rejected_artifact_count)
        print("Clean Data Ratio:", self.clean_ratio_pct, "%")
        print("============================================")


fn suppress_ocular_artifacts(
    raw_signal: List[Float64],
    z_threshold: Float64
) -> Tuple[List[Float64], ArtifactFilterStats]:
    """
    Suppresses extreme ocular (EOG blink) and muscular (EMG) artifacts using Z-score thresholding.
    Replaces corrupted samples with linear interpolation or zero-boundary clamp.
    """
    var n = len(raw_signal)
    var clean_signal = List[Float64]()
    if n == 0:
        return clean_signal, ArtifactFilterStats(0, 0)

    # 1. Compute Mean and Standard Deviation
    var sum_val: Float64 = 0.0
    for i in range(n):
        sum_val += raw_signal[i]
    var mean = sum_val / Float64(n)

    var sum_sq_diff: Float64 = 0.0
    for i in range(n):
        var diff = raw_signal[i] - mean
        sum_sq_diff += diff * diff
    var std_dev = sqrt(sum_sq_diff / Float64(n))
    if std_dev == 0.0:
        std_dev = 1.0

    var rejected_count = 0

    # 2. Filter / Clamp
    for i in range(n):
        var z_score = (raw_signal[i] - mean) / std_dev
        if z_score > z_threshold or z_score < -z_threshold:
            # Artifact detected (e.g. eye blink spike)
            clean_signal.append(mean)
            rejected_count += 1
        else:
            clean_signal.append(raw_signal[i])

    var stats = ArtifactFilterStats(n, rejected_count)
    return clean_signal, stats


fn detect_p300_erp(
    epoch_signal: List[Float64],
    sampling_rate_hz: Int,
    stimulus_onset_idx: Int
) -> ERPDetectionResult:
    """
    Scans the 250ms - 500ms post-stimulus window for a characteristic positive deflection (P300).
    """
    var n = len(epoch_signal)
    var window_start_idx = stimulus_onset_idx + Int(Float64(sampling_rate_hz) * 0.25)
    var window_end_idx = stimulus_onset_idx + Int(Float64(sampling_rate_hz) * 0.50)

    if window_start_idx >= n or window_end_idx > n or window_start_idx >= window_end_idx:
        return ERPDetectionResult(0.0, 0.0, False, 0.0)

    var max_val = epoch_signal[window_start_idx]
    var max_idx = window_start_idx

    for i in range(window_start_idx, window_end_idx):
        if epoch_signal[i] > max_val:
            max_val = epoch_signal[i]
            max_idx = i

    var latency_ms = (Float64(max_idx - stimulus_onset_idx) / Float64(sampling_rate_hz)) * 1000.0
    var is_p300 = max_val > 10.0 # Standard uV threshold for evoked potential
    var confidence = min(max_val / 20.0, 1.0) if is_p300 else 0.0

    return ERPDetectionResult(latency_ms, max_val, is_p300, confidence)


fn main():
    print("Initializing AETERNA Neuro Artifact & ERP Engine...")
    var n = 256
    var sampling_rate = 256
    var raw_samples = List[Float64]()

    # Generate signal with normal cognitive rhythm + 1 massive blink spike at sample 50
    for i in range(n):
        var val = 5.0 # baseline
        if i == 50:
            val = 150.0 # Ocular artifact (150 uV blink)
        elif i >= 70 and i <= 100: # Simulated P300 wave (approx 300ms post stimulus at sample 20)
            val = 15.0
        raw_samples.append(val)

    var clean_data, stats = suppress_ocular_artifacts(raw_samples, 2.5)
    stats.print_summary()

    var erp_result = detect_p300_erp(clean_data, sampling_rate, 20)
    erp_result.print_report()
