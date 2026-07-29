// ═══════════════════════════════════════════════════════════════════════════════
// AETERNA-SCW // SOP_STREAM_ACQUISITION.zig
// WP1: Optical Monitoring & Ingestion Upgrade
// Zero-Copy PCIe DMA State of Polarization (SOP) & Distributed Acoustic
// Sensing (DAS) Stream Acquisition Engine
// ═══════════════════════════════════════════════════════════════════════════════
// Complexity: O(1) per frame parse, O(n) for batch ingestion
// Author: Dimitar Prodromov, AETERNA Pomorie BG
// ABI: C-compatible extern for FFI binding with Rust sovereign_sentinel.rs
// ═══════════════════════════════════════════════════════════════════════════════

const std = @import("std");

// ─────────────────────────────────────────────────────────────────────────────
// § SIMD-Aligned Optical Signal Frame (C-ABI Compatible)
// ─────────────────────────────────────────────────────────────────────────────
// Layout: 16-lane SIMD vectors for AVX-512 / ARM Neon alignment.
// Total size: 8 + 8 + 64 + 64 = 144 bytes (deterministic, no padding)
// ─────────────────────────────────────────────────────────────────────────────
pub const SIMD_LANES: usize = 16;

pub const SignalFrame = extern struct {
    timestamp: u64,        // Unix epoch nanoseconds from interrogator clock
    sensor_id: u64,        // PIC-derived sensor identification (e.g., 865986222)
    phase_shift: [SIMD_LANES]f32,        // DAS coherent phase delta per km segment
    polarization_drift: [SIMD_LANES]f32, // SOP Stokes parameter drift per km segment
};

pub const FrameBatchHeader = extern struct {
    batch_id: u64,
    frame_count: u32,
    interrogator_hz: u32,  // Sampling rate of the coherent interrogator (e.g., 10000 Hz)
    cable_id: u64,         // Unique identifier for the submarine cable trunk
};

// ─────────────────────────────────────────────────────────────────────────────
// § Integer-Only Normalization (SCADA-Safe, Zero Float Drift)
// ─────────────────────────────────────────────────────────────────────────────
// Converts raw f32 phase readings to fixed-point integer representation
// for safe transport to the AIGIS Dome SCADA control plane.
// Scale factor: 1_000_000 (microsecond precision)
// ─────────────────────────────────────────────────────────────────────────────
pub const FIXED_POINT_SCALE: i64 = 1_000_000;

pub const IntegerFrame = extern struct {
    timestamp: u64,
    sensor_id: u64,
    phase_shift_fixed: [SIMD_LANES]i64,
    polarization_drift_fixed: [SIMD_LANES]i64,
};

export fn normalize_frame_to_integer(frame: *const SignalFrame, out: *IntegerFrame) void {
    out.timestamp = frame.timestamp;
    out.sensor_id = frame.sensor_id;
    for (0..SIMD_LANES) |i| {
        out.phase_shift_fixed[i] = @as(i64, @intFromFloat(frame.phase_shift[i] * @as(f32, @floatFromInt(FIXED_POINT_SCALE))));
        out.polarization_drift_fixed[i] = @as(i64, @intFromFloat(frame.polarization_drift[i] * @as(f32, @floatFromInt(FIXED_POINT_SCALE))));
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// § Zero-Copy Frame Parser (Single Frame)
// ─────────────────────────────────────────────────────────────────────────────
// Reads raw PCIe DMA buffer and extracts one SIMD-aligned optical frame.
// Returns false on buffer underrun (prevents OOB read).
// ─────────────────────────────────────────────────────────────────────────────
export fn parse_optical_frame(raw_buffer_ptr: [*]const u8, length: usize, out_frame: *SignalFrame) bool {
    if (length < @sizeOf(SignalFrame)) {
        return false; // Buffer underrun — reject without hallucination
    }

    const frame_ptr = @as(*const SignalFrame, @ptrCast(@alignCast(raw_buffer_ptr)));
    out_frame.* = frame_ptr.*;
    return true;
}

// ─────────────────────────────────────────────────────────────────────────────
// § Batch Frame Ingestion (Multi-Channel DAS/SOP)
// ─────────────────────────────────────────────────────────────────────────────
// Parses N consecutive frames from a contiguous DMA ring buffer.
// Returns the number of successfully parsed frames.
// ─────────────────────────────────────────────────────────────────────────────
export fn ingest_frame_batch(
    raw_buffer_ptr: [*]const u8,
    total_length: usize,
    out_frames: [*]SignalFrame,
    max_frames: usize,
) u32 {
    const frame_size = @sizeOf(SignalFrame);
    var offset: usize = 0;
    var count: u32 = 0;

    while (offset + frame_size <= total_length and count < max_frames) {
        const frame_ptr = @as(*const SignalFrame, @ptrCast(@alignCast(raw_buffer_ptr + offset)));
        out_frames[count] = frame_ptr.*;
        offset += frame_size;
        count += 1;
    }

    return count;
}

// ─────────────────────────────────────────────────────────────────────────────
// § Signal Magnitude Calculator (Euclidean Norm)
// ─────────────────────────────────────────────────────────────────────────────
export fn compute_frame_magnitude(frame: *const SignalFrame) f32 {
    var sum: f32 = 0.0;
    for (0..SIMD_LANES) |i| {
        sum += frame.phase_shift[i] * frame.phase_shift[i];
        sum += frame.polarization_drift[i] * frame.polarization_drift[i];
    }
    return @sqrt(sum);
}

// ═══════════════════════════════════════════════════════════════════════════════
// § VERITAS DOME: Mathematical Alignment & Safety Tests
// ═══════════════════════════════════════════════════════════════════════════════
test "SignalFrame is exactly 144 bytes (C-ABI deterministic)" {
    try std.testing.expectEqual(144, @sizeOf(SignalFrame));
}

test "SignalFrame alignment is 8 bytes (u64 anchor)" {
    try std.testing.expectEqual(8, @alignOf(SignalFrame));
}

test "IntegerFrame is exactly 272 bytes" {
    // 8 + 8 + 16*8 + 16*8 = 272
    try std.testing.expectEqual(272, @sizeOf(IntegerFrame));
}

test "Buffer underrun returns false (no OOB)" {
    const small_buffer = [_]u8{0} ** 100;
    var frame: SignalFrame = undefined;
    const result = parse_optical_frame(&small_buffer, small_buffer.len, &frame);
    try std.testing.expectEqual(false, result);
}

test "Valid 144-byte buffer parses correctly" {
    var valid_buffer = [_]u8{0} ** 144;
    const timestamp_val: u64 = 1779268878;
    std.mem.writeInt(u64, valid_buffer[0..8], timestamp_val, std.builtin.Endian.little);

    var frame: SignalFrame = undefined;
    const result = parse_optical_frame(&valid_buffer, valid_buffer.len, &frame);
    try std.testing.expectEqual(true, result);

    const builtin = @import("builtin");
    if (builtin.target.cpu.arch.endian() == std.builtin.Endian.little) {
        try std.testing.expectEqual(timestamp_val, frame.timestamp);
    }
}

test "Batch ingestion parses exactly N frames from contiguous buffer" {
    const frame_size = @sizeOf(SignalFrame);
    var buffer = [_]u8{0} ** (frame_size * 3);
    var frames: [4]SignalFrame = undefined;

    const count = ingest_frame_batch(&buffer, buffer.len, &frames, 4);
    try std.testing.expectEqual(@as(u32, 3), count);
}

test "Integer normalization preserves sign and scale" {
    var frame = SignalFrame{
        .timestamp = 100,
        .sensor_id = 200,
        .phase_shift = [_]f32{0.0} ** SIMD_LANES,
        .polarization_drift = [_]f32{0.0} ** SIMD_LANES,
    };
    frame.phase_shift[0] = 1.5;
    frame.phase_shift[1] = -0.75;

    var int_frame: IntegerFrame = undefined;
    normalize_frame_to_integer(&frame, &int_frame);

    try std.testing.expectEqual(@as(i64, 1_500_000), int_frame.phase_shift_fixed[0]);
    try std.testing.expectEqual(@as(i64, -750_000), int_frame.phase_shift_fixed[1]);
}

test "Magnitude computation is mathematically correct" {
    var frame = SignalFrame{
        .timestamp = 0,
        .sensor_id = 0,
        .phase_shift = [_]f32{0.0} ** SIMD_LANES,
        .polarization_drift = [_]f32{0.0} ** SIMD_LANES,
    };
    frame.phase_shift[0] = 3.0;
    frame.polarization_drift[0] = 4.0;

    const mag = compute_frame_magnitude(&frame);
    // sqrt(9 + 16) = 5.0
    try std.testing.expectApproxEqAbs(@as(f32, 5.0), mag, 0.001);
}
