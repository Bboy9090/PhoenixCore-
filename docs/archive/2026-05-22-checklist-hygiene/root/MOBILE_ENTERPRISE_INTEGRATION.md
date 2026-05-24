# Phoenix Core Mobile + Enterprise Integration Guide

## Overview

This guide explains how the Phoenix Core mobile app (Expo/React Native) integrates with the Phoenix Core Enterprise backend system to provide seamless device management and monitoring across platforms.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Mobile App (iOS/Android)               │
│              (Expo/React Native)                         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Screens:                                        │  │
│  │  - Devices (detection, mount, unmount, erase)   │  │
│  │  - Monitor (CPU, memory, disk metrics)          │  │
│  │  - Settings (backend configuration)             │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ REST API + WebSocket
┌────────────────────▼────────────────────────────────────┐
│              Phoenix Core Enterprise Backend             │
│                  (FastAPI - Python)                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  30+ REST Endpoints:                             │  │
│  │  - Storage device management                     │  │
│  │  - System metrics and monitoring                 │  │
│  │  - Hardware profiling                            │  │
│  │  - USB creation and recipes                      │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ System Calls
┌────────────────────▼────────────────────────────────────┐
│           Operating System (Windows/macOS/Linux)         │
│                                                          │
│  USB Devices | SSDs | HDDs | Virtual Disks             │
└──────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### 1. Start the Enterprise Backend

```bash
cd /path/to/phoenix-core-enterprise
pip install -r requirements.txt
python main_enhanced.py
```

The backend will be available at: `http://localhost:8000`

### 2. Configure Mobile App

Edit `phoenix-core-mobile/.env` (create if doesn't exist):

```env
# Backend URL (local network)
EXPO_PUBLIC_BACKEND_URL=http://192.168.1.100:8000

# Or for local development
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Install Mobile Dependencies

```bash
cd phoenix-core-mobile
pnpm install
```

### 4. Start Mobile App (Development)

```bash
# Web version
pnpm dev

# iOS
pnpm ios

# Android
pnpm android
```

---

## API Client Usage

### Initialize Client

```typescript
import { phoenixClient } from '@/lib/api/phoenix-enterprise-client';

// Set backend URL (optional, defaults to localhost:8000)
phoenixClient.setBackendUrl('http://192.168.1.100:8000');

// Verify connection
const health = await phoenixClient.healthCheck();
console.log('Backend status:', health.status);
```

### Get All Devices

```typescript
const devices = await phoenixClient.getAllDevices();
devices.forEach(device => {
  console.log(`${device.device_name}: ${device.size_bytes} bytes`);
});
```

### Get Specific Device Type

```typescript
// USB drives only
const usb = await phoenixClient.getUSBDevices();

// SSDs only
const ssds = await phoenixClient.getSSDDevices();

// HDDs only
const hdds = await phoenixClient.getHDDDevices();

// Virtual disks only
const vdd = await phoenixClient.getVirtualDevices();
```

### Mount/Unmount Device

```typescript
// Mount device
const result = await phoenixClient.mountDevice('sda1');
if (result.success) {
  console.log('Mounted at:', result.mount_point);
}

// Unmount device
const result = await phoenixClient.unmountDevice('sda1');
if (result.success) {
  console.log('Device unmounted');
}
```

### Erase Device

```typescript
// Erase and format device
const result = await phoenixClient.eraseDevice('sda1', 'ext4');
if (result.success) {
  console.log('Erase job started:', result.job_id);
}
```

### Get System Metrics

```typescript
const metrics = await phoenixClient.getSystemMetrics();
console.log(`CPU: ${metrics.cpu_percent}%`);
console.log(`Memory: ${metrics.memory_percent}%`);
console.log(`Disk: ${metrics.disk_percent}%`);
```

### Get Hardware Profile

```typescript
const hardware = await phoenixClient.getHardwareProfile();
console.log(`CPU: ${hardware.cpu_model}`);
console.log(`RAM: ${hardware.ram_gb} GB`);
console.log(`OS: ${hardware.os_name} ${hardware.os_version}`);
```

### USB Creation Workflow

```typescript
// Get available recipes
const recipes = await phoenixClient.getRecipes();

// Get specific recipe
const recipe = await phoenixClient.getRecipe('ubuntu-22.04');

// Perform safety check
const safetyCheck = await phoenixClient.safetyCheck('sda1', 'ubuntu-22.04');
if (safetyCheck.safe) {
  // Start build
  const job = await phoenixClient.startBuild('sda1', 'ubuntu-22.04');
  console.log('Build job started:', job.job_id);

  // Monitor progress
  const progress = await phoenixClient.getBuildProgress(job.job_id);
  console.log(`Progress: ${progress.progress_percent}%`);
}
```

### Real-Time Updates (WebSocket)

```typescript
// Subscribe to real-time updates
const unsubscribe = phoenixClient.subscribeToUpdates((data) => {
  console.log('Update received:', data);
  
  if (data.type === 'device_connected') {
    console.log('New device connected:', data.device);
  } else if (data.type === 'device_disconnected') {
    console.log('Device disconnected:', data.device_id);
  } else if (data.type === 'metrics_update') {
    console.log('Metrics updated:', data.metrics);
  }
});

// Unsubscribe when done
unsubscribe();
```

---

## Mobile Screens

### Devices Screen (`app/(tabs)/devices.tsx`)

Features:
- Real-time device detection
- Device type filtering (USB, SSD, HDD, VDD)
- Storage summary (total, used, free)
- Mount/unmount devices
- Erase devices
- Auto-refresh every 5 seconds

### Monitor Screen (`app/(tabs)/monitor.tsx`)

Features:
- Real-time CPU usage
- Memory usage with breakdown
- Disk usage with breakdown
- Hardware information (CPU, RAM, GPU)
- System information (OS, hostname, architecture)
- Auto-refresh every 2 seconds

### Settings Screen (to be added)

Features:
- Backend URL configuration
- Connection status
- Authentication settings
- Auto-refresh interval configuration
- Notification preferences

---

## React Query Integration

All data fetching uses React Query for caching and synchronization:

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

// Query example
const { data: devices, isLoading, refetch } = useQuery({
  queryKey: ['devices'],
  queryFn: () => phoenixClient.getAllDevices(),
  refetchInterval: 5000, // Auto-refresh every 5 seconds
});

// Mutation example
const mountMutation = useMutation({
  mutationFn: (deviceId: string) => phoenixClient.mountDevice(deviceId),
  onSuccess: () => {
    // Invalidate cache and refetch
    queryClient.invalidateQueries({ queryKey: ['devices'] });
  },
});
```

---

## Network Configuration

### Local Network Access

To access the backend from your phone on the local network:

1. Find your computer's local IP:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # Windows
   ipconfig
   ```

2. Set the backend URL in `.env`:
   ```env
   EXPO_PUBLIC_BACKEND_URL=http://192.168.1.100:8000
   ```

3. Ensure firewall allows port 8000

### Remote Access (SSH Tunnel)

For accessing from outside your network:

```bash
ssh -L 8000:localhost:8000 user@remote-host
```

Then set backend URL to: `http://localhost:8000`

---

## Error Handling

The API client includes comprehensive error handling:

```typescript
try {
  const devices = await phoenixClient.getAllDevices();
} catch (error: any) {
  if (error.response?.status === 404) {
    console.error('Backend not found');
  } else if (error.response?.status === 500) {
    console.error('Server error:', error.response.data.error);
  } else if (error.code === 'ECONNREFUSED') {
    console.error('Cannot connect to backend');
  } else {
    console.error('Unknown error:', error.message);
  }
}
```

---

## Testing

### Test Backend Connection

```bash
curl http://localhost:8000/api/health
```

### Test Device Detection

```bash
curl http://localhost:8000/api/storage/devices | jq .
```

### Test System Metrics

```bash
curl http://localhost:8000/api/system/metrics | jq .
```

---

## Troubleshooting

### Backend Not Reachable

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Check firewall settings
3. Verify backend URL in mobile app configuration
4. Check network connectivity

### Devices Not Detected

1. Verify devices are connected to the computer
2. Check device permissions (may need sudo on Linux/macOS)
3. Restart backend service

### Slow Performance

1. Reduce auto-refresh interval if too frequent
2. Use local network instead of remote access
3. Check network bandwidth
4. Monitor backend resource usage

---

## Deployment

### Production Deployment

For production use:

1. Use HTTPS with proper SSL certificates
2. Implement authentication/authorization
3. Use a reverse proxy (nginx, Apache)
4. Run backend as a service
5. Implement rate limiting
6. Add monitoring and logging

### Docker Deployment

```bash
# Build backend image
cd phoenix-core-enterprise
docker build -t phoenix-core:latest .

# Run container
docker run -p 8000:8000 --device=/dev/sda:/dev/sda phoenix-core:latest
```

---

## Future Enhancements

- [ ] WebSocket real-time updates
- [ ] Offline mode with local caching
- [ ] Push notifications for device events
- [ ] Multi-device management
- [ ] Advanced scheduling
- [ ] Cloud synchronization
- [ ] Advanced analytics
- [ ] Machine learning predictions

---

## Support

For issues or questions:

1. Check the API documentation: `http://localhost:8000/api/docs`
2. Review logs: `tail -f /var/log/phoenix-core.log`
3. Check GitHub issues
4. Contact support team

---

## Version Information

- **Mobile App**: Expo 54.0 + React Native 0.81
- **Backend**: FastAPI + Python 3.8+
- **API Client**: TypeScript with Axios
- **Data Fetching**: React Query 5.90+

---

**Last Updated**: March 31, 2026
