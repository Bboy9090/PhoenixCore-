"""
Phoenix Core API Data Models
Pydantic schemas for all API request/response types
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ─── Enums ────────────────────────────────────────────────────────────────────

class OSType(str, Enum):
    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"
    CUSTOM = "custom"

class BuildStatus(str, Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    FORMATTING = "formatting"
    WRITING = "writing"
    VERIFYING = "verifying"
    PATCHING = "patching"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PartitionScheme(str, Enum):
    GPT = "gpt"
    MBR = "mbr"
    APM = "apm"

class FilesystemType(str, Enum):
    FAT32 = "fat32"
    EXFAT = "exfat"
    NTFS = "ntfs"
    EXT4 = "ext4"
    APFS = "apfs"
    HFS_PLUS = "hfs+"


# ─── Device / USB Models ──────────────────────────────────────────────────────

class PartitionInfo(BaseModel):
    id: str
    label: Optional[str] = None
    filesystem: Optional[str] = None
    size_bytes: int
    size_human: str
    mount_points: List[str] = []

class USBDevice(BaseModel):
    id: str
    path: str
    name: str
    friendly_name: str
    size_bytes: int
    size_human: str
    size_gb: float
    removable: bool
    is_system_disk: bool
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    filesystem: Optional[str] = None
    mount_point: Optional[str] = None
    partitions: List[PartitionInfo] = []
    health_status: str = "unknown"
    write_speed_mbps: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.LOW

class DeviceListResponse(BaseModel):
    devices: List[USBDevice]
    total: int
    scan_time_ms: float
    host_os: str
    timestamp: str


# ─── Hardware Models ──────────────────────────────────────────────────────────

class CPUInfo(BaseModel):
    name: str
    manufacturer: str
    architecture: str
    cores_physical: int
    cores_logical: int
    frequency_mhz: float
    usage_percent: float

class MemoryInfo(BaseModel):
    total_bytes: int
    total_human: str
    available_bytes: int
    used_bytes: int
    percent: float

class GPUInfo(BaseModel):
    name: str
    vendor: str
    vram_bytes: Optional[int] = None

class StorageDevice(BaseModel):
    name: str
    path: str
    size_bytes: int
    size_human: str
    filesystem: Optional[str] = None
    mount_point: Optional[str] = None
    is_removable: bool

class HardwareProfile(BaseModel):
    system_name: str
    manufacturer: str
    model: str
    platform: str
    platform_version: str
    architecture: str
    cpu: CPUInfo
    memory: MemoryInfo
    gpus: List[GPUInfo] = []
    storage: List[StorageDevice] = []
    bios_version: Optional[str] = None
    serial_number: Optional[str] = None
    detection_confidence: str = "high"
    oclp_compatible: bool = False
    recommended_os: List[str] = []


# ─── System Monitor Models ────────────────────────────────────────────────────

class DiskIOStats(BaseModel):
    read_bytes: int
    write_bytes: int
    read_count: int
    write_count: int

class NetworkStats(BaseModel):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int

class SystemMetrics(BaseModel):
    cpu_percent: float
    cpu_per_core: List[float]
    memory_percent: float
    memory_used_bytes: int
    memory_total_bytes: int
    swap_percent: float
    disk_usage_percent: float
    disk_io: DiskIOStats
    network: NetworkStats
    temperature: Optional[float] = None
    uptime_seconds: float
    load_average: List[float]
    process_count: int
    timestamp: str


# ─── USB Build Models ─────────────────────────────────────────────────────────

class BuildRecipe(BaseModel):
    id: str
    name: str
    os_type: OSType
    description: str
    required_size_gb: float
    partition_scheme: PartitionScheme
    filesystem: FilesystemType
    supports_oclp: bool = False
    supports_multiboot: bool = False
    estimated_time_minutes: int
    steps: List[str]

class BuildRequest(BaseModel):
    recipe_id: str
    target_device_path: str
    os_image_path: Optional[str] = None
    os_image_url: Optional[str] = None
    hardware_profile: Optional[str] = None
    oclp_enabled: bool = False
    oclp_target_model: Optional[str] = None
    oclp_macos_version: Optional[str] = None
    dry_run: bool = False
    confirmation_token: Optional[str] = None
    options: Dict[str, Any] = {}

class BuildProgress(BaseModel):
    job_id: str
    status: BuildStatus
    progress_percent: float
    current_step: str
    steps_completed: int
    steps_total: int
    bytes_written: int
    bytes_total: int
    elapsed_seconds: float
    estimated_remaining_seconds: Optional[float] = None
    speed_mbps: Optional[float] = None
    log_messages: List[str] = []
    error: Optional[str] = None

class BuildJobResponse(BaseModel):
    job_id: str
    status: BuildStatus
    message: str
    confirmation_token: Optional[str] = None
    estimated_time_minutes: int = 0

class SafetyCheckRequest(BaseModel):
    device_path: str
    recipe_id: str

class SafetyCheckResponse(BaseModel):
    safe_to_proceed: bool
    risk_level: RiskLevel
    warnings: List[str]
    errors: List[str]
    confirmation_token: str
    device_info: Optional[USBDevice] = None


# ─── OS Image Models ──────────────────────────────────────────────────────────

class OSImageInfo(BaseModel):
    id: str
    name: str
    os_type: OSType
    version: str
    architecture: str
    size_bytes: int
    size_human: str
    checksum_sha256: Optional[str] = None
    download_url: Optional[str] = None
    local_path: Optional[str] = None
    verified: bool = False
    description: str

class OSImageDownloadRequest(BaseModel):
    image_id: str
    destination_path: Optional[str] = None

class OSImageDownloadProgress(BaseModel):
    image_id: str
    status: str
    progress_percent: float
    bytes_downloaded: int
    bytes_total: int
    speed_mbps: float
    eta_seconds: Optional[float] = None


# ─── OCLP Models ─────────────────────────────────────────────────────────────

class OCLPConfig(BaseModel):
    target_model: str
    target_macos_version: str
    enable_graphics_kext: bool = True
    enable_audio_kext: bool = True
    enable_wifi_kext: bool = True
    enable_usb_kext: bool = True
    disable_sip: bool = False
    verbose_boot: bool = False
    secure_boot_model: str = "Disabled"

class OCLPCompatibilityResult(BaseModel):
    model: str
    compatible: bool
    supported_macos_versions: List[str]
    required_kexts: List[str]
    warnings: List[str]
    notes: str


# ─── Workflow Models ──────────────────────────────────────────────────────────

class WorkflowStep(BaseModel):
    id: str
    name: str
    action: str
    params: Dict[str, Any] = {}
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    created_at: str

class WorkflowRunResult(BaseModel):
    workflow_id: str
    status: str
    steps_completed: int
    steps_total: int
    elapsed_seconds: float
    report: Optional[Dict[str, Any]] = None
    errors: List[str] = []


# ─── API Response Wrappers ────────────────────────────────────────────────────

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    platform: str
    features: Dict[str, bool]
    timestamp: str
