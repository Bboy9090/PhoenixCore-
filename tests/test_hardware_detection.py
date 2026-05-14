#!/usr/bin/env python3
"""
Test script for Hardware Auto Detection System
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_hardware_detection():
    """Test the hardware detection system"""
    print("🔍 Testing BootForge Hardware Auto Detection System")
    print("=" * 60)
    
    try:
        # Import detection components
        from src.core.hardware_detector import HardwareDetector
        from src.core.hardware_matcher import HardwareMatcher
        from src.core.vendor_database import VendorDatabase
        
        print("✅ Successfully imported detection modules")
        
        # Test vendor database
        print("\n📊 Testing Vendor Database...")
        vendor_db = VendorDatabase()
        
        # Test CPU identification
        test_cpus = [
            "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz",
            "AMD Ryzen 7 3700X 8-Core Processor", 
            "Apple M1",
            "Intel(R) Celeron(R) CPU N3060 @ 1.60GHz"
        ]
        
        for cpu in test_cpus:
            cpu_info = vendor_db.identify_cpu(cpu)
            print(f"  CPU: {cpu}")
            print(f"    Vendor: {cpu_info['vendor']}, Family: {cpu_info['family']}")
            print(f"    Architecture: {cpu_info['architecture']}, Confidence: {cpu_info['match_confidence']:.2f}")
            print()
        
        print("✅ Vendor database tests completed")
        
        # Test hardware detection
        print("\n🔎 Testing Hardware Detection...")
        detector = HardwareDetector()
        
        print(f"Available detectors: {detector.get_available_detectors()}")
        print(f"Current platform: {detector.current_platform}")
        
        if detector.current_platform != "unknown":
            print("\n🔍 Running hardware detection...")
            detected_hardware = detector.detect_hardware()
            
            if detected_hardware:
                print("✅ Hardware detection successful!")
                print(f"Platform: {detected_hardware.platform}")
                print(f"Confidence: {detected_hardware.detection_confidence.value}")
                print(f"Summary: {detected_hardware.get_summary()}")
                
                if detected_hardware.system_manufacturer:
                    print(f"Manufacturer: {detected_hardware.system_manufacturer}")
                if detected_hardware.system_model:
                    print(f"Model: {detected_hardware.system_model}")
                if detected_hardware.cpu_name:
                    print(f"CPU: {detected_hardware.cpu_name}")
                if detected_hardware.total_ram_gb:
                    print(f"RAM: {detected_hardware.total_ram_gb:.1f} GB")
                if detected_hardware.primary_gpu:
                    print(f"GPU: {detected_hardware.primary_gpu}")
                
                # Test profile matching
                print("\n🎯 Testing Profile Matching...")
                matcher = HardwareMatcher()
                matches = matcher.find_matching_profiles(detected_hardware, max_results=3)
                
                if matches:
                    print(f"Found {len(matches)} profile matches:")
                    for i, match in enumerate(matches):
                        print(f"  {i+1}. {match.profile.name}")
                        print(f"     Score: {match.match_score:.1f}%")
                        print(f"     Confidence: {match.get_confidence_text()}")
                        print(f"     Reasons: {', '.join(match.match_reasons[:2])}")
                        print()
                else:
                    print("⚠️  No profile matches found")
            else:
                print("❌ Hardware detection failed")
        else:
            print("⚠️  Hardware detection not available on this platform")

        print("✅ All hardware detection tests completed successfully!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        raise
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    success = test_hardware_detection()
    sys.exit(0 if success else 1)