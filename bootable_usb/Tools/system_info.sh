#!/bin/bash
echo "System Information"
echo "=================="
echo "macOS Version: $(sw_vers -productVersion)"
echo "Hardware: $(system_profiler SPHardwareDataType | grep 'Model Name')"
echo "Memory: $(system_profiler SPHardwareDataType | grep 'Memory')"
echo "Storage: $(df -h /)"
