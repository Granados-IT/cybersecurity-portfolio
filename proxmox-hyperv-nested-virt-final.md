# Running Proxmox VE inside Hyper-V on Windows 11 Home

Technical notes from building a SOC home lab on top of a Windows 11 Home machine. This documents what actually happened — the failed attempts, the root causes, and what eventually worked. Written so that someone in the same situation doesn't spend days on the same dead ends.

---

## Environment

- Host: Windows 11 Home 25H2
- CPU: AMD Ryzen 9800X3D
- RAM: 96 GB
- Goal: nested virtualization stack to run a SOC lab — Windows Server 2022 as Domain Controller, Kali Linux as attacker, Wazuh as SIEM, all inside Proxmox

The target architecture:

```
Windows 11 (physical host)
  └── Hyper-V
        └── Proxmox VE 8.4
              ├── Windows Server 2022 (DC)
              ├── Kali Linux
              └── Wazuh SIEM
```

For Proxmox to run KVM-accelerated VMs, it needs the CPU to expose AMD-V/SVM. In a nested setup, that means the hypervisor above Proxmox has to pass those extensions through. This is nested virtualization, and it's where most of the problems live.

---

## What didn't work and why

### VirtualBox

The natural first choice. Free, already in use, and it has a setting for nested virtualization:

```bash
VBoxManage modifyvm "proxmox" --nested-hw-virt on
```

This runs without error. It doesn't work. On AMD processors, VirtualBox doesn't reliably expose SVM to guest VMs regardless of what the setting says. Inside Proxmox, `egrep -c '(vmx|svm)' /proc/cpuinfo` returns 0. Without KVM, Proxmox falls back to software emulation (TCG), which is too slow to be usable and causes Windows Server to BSOD on boot.

This is a known limitation that doesn't get mentioned clearly enough. If you're on Intel it may behave differently. On AMD, don't bother.

### Disabling Hyper-V via bcdedit

```powershell
bcdedit /set hypervisorlaunchtype off
```

Doesn't help. On Windows 11 with Memory Integrity (HVCI) enabled, Virtualization Based Security keeps a hypervisor active at the firmware level regardless of this setting. AMD-V stays locked.

### VMware Workstation

Discarded without deep testing. With Memory Integrity on, VMware can't pass AMD-V through for nested virtualization. Disabling Memory Integrity on a machine that runs executables from unofficial sources is not a reasonable trade-off.

---

## What worked: Hyper-V on Windows 11 Home

Hyper-V is not included in Windows 11 Home by default, but the binaries are present. It can be installed with DISM.

Create a `.bat` file with the following content and run it as administrator from CMD — not PowerShell, the syntax is incompatible:

```batch
pushd "%~dp0"
dir /b %SystemRoot%\servicing\Packages\*Hyper-V*.mum >hyper-v.txt
for /f %%i in ('findstr /i . hyper-v.txt 2^>nul') do dism /online /norestart /add-package:"%SystemRoot%\servicing\Packages\%%i"
del hyper-v.txt
Dism /online /enable-feature /featurename:Microsoft-Hyper-V -All /LimitAccess /ALL
pause
```

Reboot when prompted. Don't use scripts circulating on GitHub for this — several return 404 or are outdated.

Verify:
```powershell
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V
```

Once Hyper-V is running, nested virtualization for the Proxmox VM needs to be explicitly enabled. The VM must be powered off when you run this:

```powershell
Set-VMProcessor -VMName "proxmox" -ExposeVirtualizationExtensions $true
```

### Hyper-V VM settings

| Parameter | Value |
|-----------|-------|
| Generation | 2 (UEFI) |
| RAM | 32 GB minimum for installation |
| Disk | 150 GB VHDX |
| Network | External switch |
| Secure Boot | Disabled |
| CPU | 4-8 vcores |

One thing that's not documented well: VMs running inside Proxmox won't have network connectivity unless you enable **MAC address spoofing** on the Hyper-V network adapter. Without it, the bridge looks correct but traffic doesn't flow. You'll get "Destination host unreachable" on every ping.

To enable it: Hyper-V Manager → Proxmox VM → Settings → Network Adapter → Advanced Features → Enable MAC address spoofing.

---

## Proxmox version matters

Proxmox VE 9.x fails on Hyper-V Generation 2 with:

```
[ERROR] no device with valid ISO found, please check your installation medium
```

The installer doesn't detect the virtual DVD drive. Use **Proxmox VE 8.4**.

Download: https://www.proxmox.com/en/downloads/proxmox-virtual-environment/iso/proxmox-ve-8-4-iso-installer

If installation fails mid-way with an out of memory error, assign at least 32 GB RAM to the VM. You can reduce it after Proxmox is installed.

After installation, verify KVM is available:

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo
```

Should return a number greater than 0. On a 9800X3D with 8 cores exposed, it returns 8.

---

## Installing Windows Server 2022 inside Proxmox

### VM configuration

| Parameter | Value |
|-----------|-------|
| BIOS | SeaBIOS |
| CPU | 4 cores |
| RAM | 8 GB |
| Disk | 60 GB VirtIO SCSI |
| Network | VirtIO, bridge vmbr0 |

Two ISOs needed: the Windows Server 2022 installation media and `virtio-win.iso` for the drivers.

**Use SeaBIOS, not OVMF.** OVMF with Secure Boot will prevent Windows Server from booting. Change it in Hardware → BIOS before first boot.

### Disk driver during installation

The Windows installer won't detect the VirtIO disk. When it shows "We couldn't find any drives":

1. Click Load driver
2. Browse to `E:\vioscsi\2k22\amd64\` (the virtio-win CD)
3. Uncheck "Hide compatible drivers" if nothing appears
4. Select Red Hat VirtIO SCSI pass-through controller
5. Continue

### Network driver after installation

The VirtIO network adapter also needs a driver. With the virtio-win ISO mounted:

```powershell
pnputil /add-driver D:\NetKVM\2k22\amd64\netkvm.inf /install
```

Or right-click `netkvm` (Setup Information file) in `D:\NetKVM\2k22\amd64\` and install from there.

Verify with `Get-NetAdapter`. Should show Red Hat VirtIO Ethernet Adapter.

---

## Network and RDP

Assign a static IP:

```cmd
netsh interface ip set address "Ethernet" static 192.168.1.50 255.255.255.0 192.168.1.1
```

Enable RDP. The cleanest way is through the GUI: Server Manager → Local Server → Remote Desktop → click Disabled → Allow remote connections → OK.

If doing it from the command line:

```cmd
reg add "HKLM\System\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections /d 0 /f
netsh advfirewall firewall set rule group="remote desktop" new enable=Yes
net start "Remote Desktop Services"
```

If RDP still doesn't connect, the firewall may be blocking it regardless of the rule. Disabling it entirely to confirm:

```cmd
netsh advfirewall set allprofiles state off
```

Connect from Windows 11: `mstsc` → 192.168.1.50 → Administrator.

---

## Compatibility summary

| Configuration | KVM available | Notes |
|---------------|--------------|-------|
| VirtualBox + AMD | No | SVM not exposed to guest on AMD |
| VMware + Memory Integrity on | No | HVCI blocks AMD-V passthrough |
| Hyper-V + Proxmox 9.x | No | ISO not detected on Gen 2 |
| Hyper-V + Proxmox 8.4 | Yes | Working configuration |
| Proxmox bare metal | Yes | Best option when available |

---

## Current state (June 2026)

Hyper-V running on Windows 11 Home. Proxmox VE 8.4 with KVM confirmed. Windows Server 2022 installed with VirtIO drivers, static IP at 192.168.1.50, RDP accessible from the host.

Remaining: Active Directory configuration, Kali Linux VM, SIEM deployment.

---

## References

- [Proxmox VE Downloads](https://www.proxmox.com/en/downloads)
- [Hyper-V nested virtualization](https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/user-guide/nested-virtualization)
- [Set-VMProcessor](https://learn.microsoft.com/en-us/powershell/module/hyper-v/set-vmprocessor)
- [VirtIO drivers](https://github.com/virtio-win/virtio-win-pkg-scripts)
- [Farrukh Ahmet SOC Home Lab](https://github.com/farrukhCTI/soc-homelab)
