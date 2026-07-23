#!/usr/bin/env python3
"""
PhoenixCore Diagnostic Telemetry & System Health Aggregator
"""

import json
import time


class SystemHealthTelemetry:
    def __init__(self, machine_id: str):
        self.machine_id = machine_id
        self.timestamp = int(time.time())

    def collect_telemetry(
        self, ram_used_mb: int, cpu_temp_c: float, disk_iops: int
    ) -> dict:
        return {
            "machine_id": self.machine_id,
            "timestamp": self.timestamp,
            "metrics": {
                "ram_usage_mb": ram_used_mb,
                "cpu_temperature_celsius": cpu_temp_c,
                "disk_iops": disk_iops,
                "system_status": "HEALTHY" if cpu_temp_c < 85.0 else "THERMAL_WARNING",
            },
        }


if __name__ == "__main__":
    telemetry = SystemHealthTelemetry("ARCWYRE-NODE-01")
    report = telemetry.collect_telemetry(1024, 48.5, 3200)
    print(json.dumps(report, indent=2))
