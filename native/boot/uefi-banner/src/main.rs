#![no_main]
#![no_std]

extern crate alloc;

#[cfg(target_arch = "x86_64")]
use core::arch::asm;
use core::hint::spin_loop;
use alloc::vec::Vec;
use uefi::boot::{self, LoadImageSource};
use uefi::cstr16;
use uefi::fs::FileSystem;
use uefi::prelude::*;
use uefi::println;

#[cfg(target_arch = "x86_64")]
const DEBUGCON_PORT: u16 = 0x402;
#[cfg(target_arch = "x86_64")]
const KERNEL_STAGE_PATH: &uefi::CStr16 = cstr16!("\\EFI\\BOOT\\KERNELX64.EFI");
#[cfg(target_arch = "aarch64")]
const KERNEL_STAGE_PATH: &uefi::CStr16 = cstr16!("\\EFI\\BOOT\\KERNELAA64.EFI");

#[cfg(target_arch = "x86_64")]
#[inline(always)]
unsafe fn outb(port: u16, value: u8) {
    unsafe {
        asm!(
            "out dx, al",
            in("dx") port,
            in("al") value,
            options(nomem, nostack, preserves_flags)
        );
    }
}

#[cfg(target_arch = "x86_64")]
unsafe fn serial_write_byte(byte: u8) {
    unsafe {
        outb(DEBUGCON_PORT, byte);
    }
}

#[cfg(target_arch = "x86_64")]
fn serial_write_line(line: &str) {
    unsafe {
        for b in line.bytes() {
            serial_write_byte(b);
        }
        serial_write_byte(b'\r');
        serial_write_byte(b'\n');
    }
}

#[cfg(not(target_arch = "x86_64"))]
fn serial_write_line(_line: &str) {}

fn fail_with_hold(reason: &str) -> ! {
    println!("Native handoff failure: {}", reason);
    serial_write_line("Native handoff failure.");
    serial_write_line(reason);
    loop {
        spin_loop();
    }
}

#[entry]
fn main() -> Status {
    if let Err(err) = uefi::helpers::init() {
        return err.status();
    }

    println!("================================================");
    println!(" BLUE PHOENIX NATIVE :: NATIVE-0 BOOT PROOF");
    println!(" Sovereign UEFI entry reached successfully.");
    println!("================================================");
    println!("No Linux userspace is active in this artifact.");
    println!("Boot hold active for evidence capture.");

    serial_write_line("================================================");
    serial_write_line(" BLUE PHOENIX NATIVE :: NATIVE-0 BOOT PROOF");
    serial_write_line(" Sovereign UEFI entry reached successfully.");
    serial_write_line("================================================");
    serial_write_line("No Linux userspace is active in this artifact.");
    serial_write_line("Boot hold active for evidence capture.");

    println!("Loading kernel stage image...");
    serial_write_line("Loading kernel stage image...");

    let fs_proto = match boot::get_image_file_system(boot::image_handle()) {
        Ok(fs) => fs,
        Err(_) => fail_with_hold("Unable to access boot filesystem."),
    };

    let mut fs = FileSystem::new(fs_proto);
    let kernel_image: Vec<u8> = match fs.read(KERNEL_STAGE_PATH) {
        Ok(bytes) => bytes,
        Err(_) => fail_with_hold("Unable to read kernel stage EFI file."),
    };

    println!("Kernel stage bytes loaded: {}", kernel_image.len());
    serial_write_line("Kernel stage bytes loaded.");
    serial_write_line("Handing off control to kernel stage...");

    let loaded = match boot::load_image(
        boot::image_handle(),
        LoadImageSource::FromBuffer {
            buffer: kernel_image.as_slice(),
            file_path: None,
        },
    ) {
        Ok(handle) => handle,
        Err(_) => fail_with_hold("UEFI LoadImage failed for kernel stage."),
    };

    match boot::start_image(loaded) {
        Ok(()) => fail_with_hold("Kernel stage exited unexpectedly."),
        Err(_) => fail_with_hold("UEFI StartImage failed for kernel stage."),
    }
}
