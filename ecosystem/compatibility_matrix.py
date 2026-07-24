#!/usr/bin/env python3
"""
PhoenixCore Universal Hardware Compatibility Matrix Generator
"""

import json


class HardwareCompatibilityMatrix:
    def __init__(self):
        self.supported_architectures = ["x86_64", "aarch64"]
        self.supported_storage = ["AHCI_SATA", "NVME_PCIE", "USB_MASS_STORAGE"]
        self.supported_nics = ["INTEL_E1000", "REALTEK_RTL8139", "VIRTIO_NET"]

    def evaluate_device(self, arch: str, storage: str, nic: str) -> dict:
        arch_ok = arch in self.supported_architectures
        storage_ok = storage in self.supported_storage
        nic_ok = nic in self.supported_nics

        overall_pass = arch_ok and storage_ok and nic_ok

        return {
            "evaluation": {
                "architecture_supported": arch_ok,
                "storage_supported": storage_ok,
                "network_supported": nic_ok,
            },
            "compatibility_verdict": (
                "FULL_SUPPORT" if overall_pass else "PARTIAL_SUPPORT"
            ),
            "recommended_edition": (
                "ARCWYRE Eternum" if arch == "x86_64" else "ARCWYRE Native"
            ),
        }


if __name__ == "__main__":
    matrix = HardwareCompatibilityMatrix()
    res = matrix.evaluate_device("x86_64", "NVME_PCIE", "INTEL_E1000")
    print(json.dumps(res, indent=2))
