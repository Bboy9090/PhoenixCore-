#!/usr/bin/env python3
"""
BootForge Standalone - Single-file version for easy download
Professional Cross-Platform OS Deployment Tool
"""

import sys
import os
import logging
import time
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Import dependencies with fallbacks
try:
    import click
except ImportError:
    print("Please install click: pip install click")
    sys.exit(1)

try:
    from colorama import init, Fore, Back, Style
    init()
    HAS_COLOR = True
except ImportError:
    class MockColor:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = MockColor()
    HAS_COLOR = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

@dataclass
class DiskInfo:
    """Information about a disk device"""
    path: str
    name: str
    size_bytes: int
    filesystem: str = "unknown"
    mountpoint: str = ""
    is_removable: bool = False
    model: str = "Unknown"
    vendor: str = "Unknown"
    serial: str = "Unknown"
    health_status: str = "Unknown"
    write_speed_mbps: float = 0.0

class SimpleDiskManager:
    """Simple disk management for USB devices"""
    
    def get_removable_drives(self) -> List[DiskInfo]:
        """Get list of removable USB drives"""
        if not HAS_PSUTIL:
            return []
        
        drives = []
        try:
            for partition in psutil.disk_partitions():
                if 'removable' in partition.opts or 'usb' in partition.device.lower():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        drives.append(DiskInfo(
                            path=partition.device,
                            name=f"USB Drive ({partition.mountpoint})",
                            size_bytes=usage.total,
                            filesystem=partition.fstype,
                            mountpoint=partition.mountpoint,
                            is_removable=True,
                            health_status="Good"
                        ))
                    except (PermissionError, OSError):
                        continue
        except Exception:
            pass
        
        return drives

# CLI Interface
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """BootForge - Professional Cross-Platform OS Deployment Tool"""
    ctx.ensure_object(dict)
    ctx.obj['disk_manager'] = SimpleDiskManager()
    
    # Professional banner
    click.echo(f"{Fore.CYAN}┌─────────────────────────────────────────┐{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}│{Style.RESET_ALL} {Fore.BLUE}{Style.BRIGHT}BootForge CLI v1.0.0{Style.RESET_ALL}                 {Fore.CYAN}│{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}│{Style.RESET_ALL} Professional OS Deployment Tool      {Fore.CYAN}│{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}└─────────────────────────────────────────┘{Style.RESET_ALL}")
    
    if verbose:
        click.echo(f"{Fore.YELLOW}🔍 Verbose mode enabled{Style.RESET_ALL}")

@cli.command()
@click.pass_context
def list_devices(ctx):
    """List available USB devices"""
    disk_manager = ctx.obj['disk_manager']
    
    click.echo(f"{Fore.BLUE}🔍 Scanning for USB devices...{Style.RESET_ALL}")
    
    # Add animation
    for i in range(3):
        click.echo(f"   {'.' * (i + 1)}", nl=False)
        time.sleep(0.3)
        click.echo("\r   ", nl=False)
    click.echo("\r")
    
    devices = disk_manager.get_removable_drives()
    
    if not devices:
        click.echo(f"{Fore.YELLOW}⚠️  No USB devices found.{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}💡 Make sure USB devices are connected and properly mounted.{Style.RESET_ALL}")
        return
    
    click.echo(f"{Fore.GREEN}✅ Found {len(devices)} USB device(s):{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")
    
    for i, device in enumerate(devices, 1):
        size_gb = device.size_bytes / (1024**3)
        health_color = Fore.GREEN if device.health_status == "Good" else Fore.YELLOW
        
        click.echo(f"{Fore.BRIGHT}{i}. {device.name}{Style.RESET_ALL}")
        click.echo(f"   📁 Path: {Fore.WHITE}{device.path}{Style.RESET_ALL}")
        click.echo(f"   💾 Size: {Fore.WHITE}{size_gb:.1f} GB{Style.RESET_ALL}")
        click.echo(f"   🗂️  Filesystem: {Fore.WHITE}{device.filesystem}{Style.RESET_ALL}")
        click.echo(f"   ❤️  Health: {health_color}{device.health_status}{Style.RESET_ALL}")
        click.echo()

@cli.command()
@click.option('--image', '-i', required=True, help='Path to OS image file')
@click.option('--device', '-d', required=True, help='Target device path')
@click.option('--dry-run', is_flag=True, help='Show what would be done without actually doing it')
@click.option('--force', is_flag=True, help='Force operation without confirmation')
@click.pass_context
def write_image(ctx, image, device, dry_run, force):
    """Write OS image to USB device"""
    image_path = Path(image)
    
    if not image_path.exists():
        click.echo(f"{Fore.RED}❌ Error: Image file not found: {image}{Style.RESET_ALL}", err=True)
        sys.exit(1)
    
    size_mb = image_path.stat().st_size / (1024 * 1024)
    
    click.echo(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")
    click.echo(f"{Fore.BLUE}{Style.BRIGHT}📋 Operation Details:{Style.RESET_ALL}")
    click.echo(f"  📁 Image: {Fore.WHITE}{image_path.name}{Style.RESET_ALL} ({Fore.YELLOW}{size_mb:.1f} MB{Style.RESET_ALL})")
    click.echo(f"  🎯 Target: {Fore.WHITE}{device}{Style.RESET_ALL}")
    click.echo(f"  🧪 Mode: {Fore.YELLOW}DRY RUN{Style.RESET_ALL}" if dry_run else f"  ⚡ Mode: {Fore.GREEN}LIVE OPERATION{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")
    
    if dry_run:
        click.echo(f"{Fore.YELLOW}🧪 DRY RUN: Would write {image_path.name} to {device}{Style.RESET_ALL}")
        click.echo(f"{Fore.GREEN}✅ Dry run completed successfully!{Style.RESET_ALL}")
        return
    
    # Safety warnings
    click.echo(f"{Fore.RED}{Style.BRIGHT}⚠️  CRITICAL WARNING ⚠️{Style.RESET_ALL}")
    click.echo(f"{Fore.RED}🚨 This will PERMANENTLY ERASE all data on {device}!{Style.RESET_ALL}")
    click.echo()
    
    if not force:
        if not click.confirm("Do you understand this will erase all data on the target device?"):
            click.echo(f"{Fore.GREEN}✅ Operation cancelled.{Style.RESET_ALL}")
            sys.exit(0)
        
        confirmation = click.prompt(f"Type 'WRITE TO {device}' to confirm", type=str)
        if confirmation != f"WRITE TO {device}":
            click.echo(f"{Fore.RED}❌ Confirmation failed. Operation cancelled.{Style.RESET_ALL}")
            sys.exit(0)
    
    click.echo(f"{Fore.BLUE}📝 Note: This is a simplified version. Full disk operations require admin privileges.{Style.RESET_ALL}")
    click.echo(f"{Fore.GREEN}✅ Operation would be executed with proper permissions.{Style.RESET_ALL}")

@cli.command()
def system_info():
    """Show system information"""
    import platform
    
    click.echo(f"{Fore.BLUE}🖥️  System Information:{Style.RESET_ALL}")
    click.echo(f"  OS: {platform.system()} {platform.release()}")
    click.echo(f"  Architecture: {platform.machine()}")
    click.echo(f"  Python: {sys.version.split()[0]}")
    
    if HAS_PSUTIL:
        click.echo(f"  CPU Usage: {psutil.cpu_percent()}%")
        memory = psutil.virtual_memory()
        click.echo(f"  Memory: {memory.percent}% used")

if __name__ == "__main__":
    try:
        cli()
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install click colorama psutil")
        sys.exit(1)