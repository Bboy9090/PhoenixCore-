# Remote Build Agent Setup: Phoenix OS

For large-scale or automated builds, a dedicated Remote Build Agent is recommended to offload the high I/O and CPU requirements of the ISO generation process.

## Recommended Baseline Specification
- **OS**: Ubuntu 22.04 LTS or Debian 12 (Bookworm).
- **CPU**: 4+ Cores.
- **RAM**: 8GB+ (16GB recommended for parallel chroot operations).
- **Disk**: 50GB+ SSD storage.
- **Network**: High-speed internet for package fetching.

## 1. Automated Setup (Native Docker)
```bash
# Update and install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Compose
sudo apt-get install -y docker-compose-plugin
```

## 2. Remote Workflow (SSH)
The Phoenix OS workspace can be synchronized to a remote builder via `rsync` or direct `git clone`.

### Synchronization
```bash
rsync -avz --exclude 'node_modules' ./ user@build-agent:~/phoenix-core-enterprise/
```

### Remote Execution
```bash
ssh user@build-agent "cd ~/phoenix-core-enterprise/os/phoenix-os && bash container/build-container.sh"
```

## 3. Artifact Retrieval
Once the build succeeds, the ISO can be retrieved from the remote `build/` directory:
```bash
scp user@build-agent:~/phoenix-core-enterprise/os/phoenix-os/build/*.iso ./
```

## 4. Security Considerations
- **SSH Keys**: Use SSH keys for all remote agent interactions; disable password authentication.
- **Firewall**: Ensure only authorized IPs can access the build agent.
- **Clean Builds**: Configure the agent to purge the `os/phoenix-os/build` directory between major releases.
