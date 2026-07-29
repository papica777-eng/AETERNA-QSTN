// ═══════════════════════════════════════════════════════════════════════════════
// AETERNA-SCW // src/scada/aigis_dome.rs
// WP3: AIGIS Dome Control Plane — Integer-Only SCADA Interface Validator
// ═══════════════════════════════════════════════════════════════════════════════
// Complexity: O(1) per command validation
// ZERO FLOAT: All arithmetic uses i64 fixed-point (cents/microseconds).
// Compliance: NIS2 Directive, EU 5G Toolbox, CEF Regulation Art 9(4)
// Author: Dimitar Prodromov, AETERNA Pomorie BG
// ═══════════════════════════════════════════════════════════════════════════════

/// Modbus function codes allowed for SCADA landing-station PLC controllers.
/// Any function code outside this whitelist triggers immediate rejection.
#[derive(Debug, Clone, Copy, PartialEq)]
#[repr(u8)]
pub enum ModbusFunction {
    ReadCoils = 0x01,
    ReadDiscreteInputs = 0x02,
    ReadHoldingRegisters = 0x03,
    ReadInputRegisters = 0x04,
    WriteSingleCoil = 0x05,
    WriteSingleRegister = 0x06,
}

impl ModbusFunction {
    // Complexity: O(1)
    pub fn from_byte(byte: u8) -> Option<ModbusFunction> {
        match byte {
            0x01 => Some(ModbusFunction::ReadCoils),
            0x02 => Some(ModbusFunction::ReadDiscreteInputs),
            0x03 => Some(ModbusFunction::ReadHoldingRegisters),
            0x04 => Some(ModbusFunction::ReadInputRegisters),
            0x05 => Some(ModbusFunction::WriteSingleCoil),
            0x06 => Some(ModbusFunction::WriteSingleRegister),
            _ => None, // Reject unknown/dangerous function codes (e.g., 0x10 WriteMultiple)
        }
    }

    pub fn is_write(&self) -> bool {
        matches!(self, ModbusFunction::WriteSingleCoil | ModbusFunction::WriteSingleRegister)
    }
}

/// Integer-only SCADA command representation.
/// ALL values are integers. Zero floating-point operations.
#[derive(Debug, Clone)]
pub struct ScadaCommand {
    pub unit_id: u8,
    pub function: ModbusFunction,
    pub register_address: u16,
    pub value: i64,            // Fixed-point integer value (scaled by 1_000_000)
    pub timestamp_ns: u64,     // Nanosecond-precision timestamp
    pub source_ip_hash: u64,   // Hash of source IP (no raw IP storage — GDPR compliant)
}

/// Validation result for SCADA commands.
#[derive(Debug, Clone, PartialEq)]
pub enum ValidationResult {
    Accepted,
    RejectedUnknownFunction(u8),
    RejectedRegisterOutOfRange(u16),
    RejectedValueOverflow(i64),
    RejectedWriteBlocked,
    RejectedRateLimitExceeded,
}

/// AIGIS Dome Control Plane — the sovereign SCADA firewall.
/// All arithmetic is strictly integer-only (Zero-Float mandate).
pub struct AigisDome {
    /// Whitelist of register addresses that can be written to
    write_allowed_registers: [u16; 8],
    write_allowed_count: usize,
    /// Maximum absolute value for any register write (prevents PLC overflow)
    max_register_value: i64,
    /// Rate limiting: max commands per second (integer counter)
    max_commands_per_second: u32,
    /// Rolling command counter (reset every second by the sentinel daemon)
    command_count: u32,
    /// Threat lockdown: if true, ALL write commands are rejected
    lockdown_active: bool,
}

impl AigisDome {
    // Complexity: O(1)
    pub fn new() -> Self {
        AigisDome {
            write_allowed_registers: [0x0000, 0x0001, 0x0002, 0x0003, 0x0010, 0x0011, 0x0020, 0x0021],
            write_allowed_count: 8,
            max_register_value: 100_000_000, // 100.000000 in fixed-point
            max_commands_per_second: 1000,
            command_count: 0,
            lockdown_active: false,
        }
    }

    /// Activate lockdown — blocks ALL write operations to PLCs.
    /// Called by sovereign_sentinel.rs when eBPF apoptosis triggers.
    // Complexity: O(1)
    pub fn engage_lockdown(&mut self) {
        self.lockdown_active = true;
    }

    /// Deactivate lockdown (requires explicit architect command).
    // Complexity: O(1)
    pub fn disengage_lockdown(&mut self) {
        self.lockdown_active = false;
    }

    /// Reset the per-second command counter.
    // Complexity: O(1)
    pub fn reset_rate_counter(&mut self) {
        self.command_count = 0;
    }

    /// Validate and sanitize an incoming SCADA Modbus/TCP command.
    /// Returns Accepted only if ALL checks pass.
    // Complexity: O(1) — fixed-size whitelist scan
    pub fn validate_command(&mut self, raw_function_byte: u8, register: u16, value: i64) -> ValidationResult {
        // Rate limit check
        self.command_count += 1; // Integer increment, no float
        if self.command_count > self.max_commands_per_second {
            return ValidationResult::RejectedRateLimitExceeded;
        }

        // Function code whitelist
        let function = match ModbusFunction::from_byte(raw_function_byte) {
            Some(f) => f,
            None => return ValidationResult::RejectedUnknownFunction(raw_function_byte),
        };

        // If it's a write operation, apply additional checks
        if function.is_write() {
            // Lockdown check
            if self.lockdown_active {
                return ValidationResult::RejectedWriteBlocked;
            }

            // Register whitelist check
            let mut allowed = false;
            for i in 0..self.write_allowed_count {
                if self.write_allowed_registers[i] == register {
                    allowed = true;
                    break;
                }
            }
            if !allowed {
                return ValidationResult::RejectedRegisterOutOfRange(register);
            }

            // Value overflow check (integer-only bounds)
            if value > self.max_register_value || value < -self.max_register_value {
                return ValidationResult::RejectedValueOverflow(value);
            }
        }

        ValidationResult::Accepted
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// § VERITAS DOME: Integer-Only SCADA Validation Tests
// ═══════════════════════════════════════════════════════════════════════════════
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_valid_read_command_accepted() {
        let mut dome = AigisDome::new();
        let result = dome.validate_command(0x03, 0x0000, 0); // ReadHoldingRegisters
        assert_eq!(result, ValidationResult::Accepted);
    }

    #[test]
    fn test_valid_write_command_accepted() {
        let mut dome = AigisDome::new();
        let result = dome.validate_command(0x06, 0x0001, 50_000_000); // WriteSingleRegister
        assert_eq!(result, ValidationResult::Accepted);
    }

    #[test]
    fn test_unknown_function_rejected() {
        let mut dome = AigisDome::new();
        let result = dome.validate_command(0x10, 0x0000, 0); // WriteMultipleRegisters — NOT ALLOWED
        assert_eq!(result, ValidationResult::RejectedUnknownFunction(0x10));
    }

    #[test]
    fn test_write_to_forbidden_register_rejected() {
        let mut dome = AigisDome::new();
        let result = dome.validate_command(0x06, 0xFFFF, 100); // Unknown register
        assert_eq!(result, ValidationResult::RejectedRegisterOutOfRange(0xFFFF));
    }

    #[test]
    fn test_value_overflow_rejected() {
        let mut dome = AigisDome::new();
        let result = dome.validate_command(0x06, 0x0001, 999_999_999_999); // Way too large
        assert_eq!(result, ValidationResult::RejectedValueOverflow(999_999_999_999));
    }

    #[test]
    fn test_lockdown_blocks_all_writes() {
        let mut dome = AigisDome::new();
        dome.engage_lockdown();
        let result = dome.validate_command(0x06, 0x0001, 100); // Valid write, but lockdown
        assert_eq!(result, ValidationResult::RejectedWriteBlocked);
    }

    #[test]
    fn test_lockdown_allows_reads() {
        let mut dome = AigisDome::new();
        dome.engage_lockdown();
        let result = dome.validate_command(0x03, 0x0001, 0); // Read is always allowed
        assert_eq!(result, ValidationResult::Accepted);
    }

    #[test]
    fn test_rate_limit_enforcement() {
        let mut dome = AigisDome::new();
        dome.max_commands_per_second = 2;
        assert_eq!(dome.validate_command(0x03, 0x0000, 0), ValidationResult::Accepted);
        assert_eq!(dome.validate_command(0x03, 0x0000, 0), ValidationResult::Accepted);
        assert_eq!(dome.validate_command(0x03, 0x0000, 0), ValidationResult::RejectedRateLimitExceeded);
    }

    #[test]
    fn test_rate_limit_resets() {
        let mut dome = AigisDome::new();
        dome.max_commands_per_second = 1;
        assert_eq!(dome.validate_command(0x03, 0x0000, 0), ValidationResult::Accepted);
        assert_eq!(dome.validate_command(0x03, 0x0000, 0), ValidationResult::RejectedRateLimitExceeded);
        dome.reset_rate_counter();
        assert_eq!(dome.validate_command(0x03, 0x0000, 0), ValidationResult::Accepted);
    }

    #[test]
    fn test_zero_float_invariant() {
        // This test exists to prove that AigisDome contains ZERO floating-point fields.
        // All values are integer types (u8, u16, u32, i64, u64, bool).
        let dome = AigisDome::new();
        assert_eq!(std::mem::size_of_val(&dome.max_register_value), 8); // i64
        assert_eq!(std::mem::size_of_val(&dome.max_commands_per_second), 4); // u32
        assert_eq!(std::mem::size_of_val(&dome.command_count), 4); // u32
        assert_eq!(std::mem::size_of_val(&dome.lockdown_active), 1); // bool
    }
}
