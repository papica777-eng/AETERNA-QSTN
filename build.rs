use std::env;
use std::process::Command;
use std::path::PathBuf;

fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();
    let _out_path = PathBuf::from(&out_dir);

    // Compile Zig code to a static library
    let status = Command::new("zig")
        .args(&[
            "build-lib",
            "src/ingress/SOP_STREAM_ACQUISITION.zig",
            "-femit-bin=parser.lib", // Output .lib for Windows MSVC target
            "-O", "ReleaseFast",
            "-lc",
            "--name", "parser"
        ])
        .current_dir(env::current_dir().unwrap())
        .status()
        .expect("Failed to execute zig build-lib");

    assert!(status.success(), "Zig compilation failed");

    // Tell cargo to look for the library in the current directory (where zig output it)
    println!("cargo:rustc-link-search=native={}", env::current_dir().unwrap().display());
    // Tell cargo to link the static library
    println!("cargo:rustc-link-lib=static=parser");
    
    // Re-run if SOP_STREAM_ACQUISITION.zig changes
    println!("cargo:rerun-if-changed=src/ingress/SOP_STREAM_ACQUISITION.zig");
    println!("cargo:rerun-if-changed=build.rs");
}
