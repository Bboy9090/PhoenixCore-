#![no_main]
#![no_std]

#[cfg(target_arch = "x86_64")]
use core::arch::asm;
use core::hint::spin_loop;
use uefi::prelude::*;
use uefi::println;

#[cfg(target_arch = "x86_64")]
const DEBUGCON_PORT: u16 = 0x402;

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
fn debug_line(msg: &str) {
    unsafe {
        for b in msg.bytes() {
            outb(DEBUGCON_PORT, b);
        }
        outb(DEBUGCON_PORT, b'\r');
        outb(DEBUGCON_PORT, b'\n');
    }
}

#[cfg(not(target_arch = "x86_64"))]
fn debug_line(_msg: &str) {}

#[entry]
fn main() -> Status {
    if let Err(err) = uefi::helpers::init() {
        return err.status();
    }

    println!("===============================================");
    println!(" BLUE PHOENIX NATIVE :: KERNEL STUB ACTIVE");
    println!(" Stage handoff from boot manager confirmed.");
    println!("===============================================");

    debug_line("===============================================");
    debug_line(" BLUE PHOENIX NATIVE :: KERNEL STUB ACTIVE");
    debug_line(" Stage handoff from boot manager confirmed.");
    debug_line("===============================================");

    loop {
        spin_loop();
    }
}
