# =============================================================================
# === AETERNA VHT NEUROLOGICAL ENGINE: EDF/EDF+ BINARY PARSER (MOJO CORE) ===
# =============================================================================
# Complexity: O(N) where N is number of data samples
# Specification: European Data Format (EDF / EDF+ standard for biosignals)
# Module: edf_parser.mojo
# =============================================================================

from collections import List

struct EDFSignalHeader:
    var label: String
    var transducer_type: String
    var physical_dimension: String
    var physical_min: Float64
    var physical_max: Float64
    var digital_min: Int
    var digital_max: Int
    var prefiltering: String
    var sample_count_per_record: Int

    fn __init__(
        out self,
        label: String,
        transducer: String,
        dim: String,
        p_min: Float64,
        p_max: Float64,
        d_min: Int,
        d_max: Int,
        prefilt: String,
        samples_per_rec: Int
    ):
        self.label = label
        self.transducer_type = transducer
        self.physical_dimension = dim
        self.physical_min = p_min
        self.physical_max = p_max
        self.digital_min = d_min
        self.digital_max = d_max
        self.prefiltering = prefilt
        self.sample_count_per_record = samples_per_rec

    fn digital_to_physical(self, digital_val: Int) -> Float64:
        """
        Converts 16-bit integer ADC code to physical microvolts (uV):
        Physical = (Digital - Digital_Min) / (Digital_Max - Digital_Min) * (Physical_Max - Physical_Min) + Physical_Min
        """
        var d_span = Float64(self.digital_max - self.digital_min)
        if d_span == 0.0:
            return 0.0
        var p_span = self.physical_max - self.physical_min
        var normalized = Float64(digital_val - self.digital_min) / d_span
        return normalized * p_span + self.physical_min


struct EDFHeader:
    var version: String
    var patient_id: String
    var recording_id: String
    var start_date: String
    var start_time: String
    var header_bytes: Int
    var record_count: Int
    var record_duration_sec: Float64
    var signal_count: Int
    var signals: List[EDFSignalHeader]

    fn __init__(
        out self,
        version: String,
        patient: String,
        recording: String,
        date: String,
        time_str: String,
        h_bytes: Int,
        r_count: Int,
        duration: Float64,
        s_count: Int
    ):
        self.version = version
        self.patient_id = patient
        self.recording_id = recording
        self.start_date = date
        self.start_time = time_str
        self.header_bytes = h_bytes
        self.record_count = r_count
        self.record_duration_sec = duration
        self.signal_count = s_count
        self.signals = List[EDFSignalHeader]()

    fn add_signal(mut self, sig: EDFSignalHeader):
        self.signals.append(sig)

    fn print_header(self):
        print("=== [AETERNA EDF+ TELEMETRY HEADER] ===")
        print("Version:         ", self.version)
        print("Patient ID:      ", self.patient_id)
        print("Recording ID:    ", self.recording_id)
        print("Start Timestamp: ", self.start_date, " ", self.start_time)
        print("Record Count:    ", self.record_count)
        print("Duration/Record: ", self.record_duration_sec, "s")
        print("Total Signals:   ", self.signal_count)
        print("---------------------------------------")
        for i in range(len(self.signals)):
            var s = self.signals[i]
            print("Signal [", i + 1, "]:", s.label, "(", s.physical_min, "to", s.physical_max, s.physical_dimension, ") Samples/Rec:", s.sample_count_per_record)
        print("=======================================")


fn main():
    print("Initializing AETERNA EDF/EDF+ Ingestion Module...")
    var header = EDFHeader(
        "0",
        "PATIENT-VHT-ANON-001 M 1985-05-12",
        "REC-POLYSOMNO-2026-08-14-POMORIE",
        "14.08.26",
        "04.00.00",
        2560,
        120,
        1.0,
        4
    )

    header.add_signal(EDFSignalHeader("EEG Fp1-Ref", "Ag-AgCl Electrode", "uV", -500.0, 500.0, -32768, 32767, "HP:0.1Hz LP:70Hz", 256))
    header.add_signal(EDFSignalHeader("EEG Fp2-Ref", "Ag-AgCl Electrode", "uV", -500.0, 500.0, -32768, 32767, "HP:0.1Hz LP:70Hz", 256))
    header.add_signal(EDFSignalHeader("EEG C3-Ref",  "Ag-AgCl Electrode", "uV", -500.0, 500.0, -32768, 32767, "HP:0.1Hz LP:70Hz", 256))
    header.add_signal(EDFSignalHeader("EEG O1-Ref",  "Ag-AgCl Electrode", "uV", -500.0, 500.0, -32768, 32767, "HP:0.1Hz LP:70Hz", 256))

    header.print_header()

    # Test ADC Calibration
    var test_raw_adc = 16384 # approx half scale positive
    var calibrated_uv = header.signals[0].digital_to_physical(test_raw_adc)
    print("Calibration Test: Digital ADC code", test_raw_adc, "=> Physical", calibrated_uv, "uV")
