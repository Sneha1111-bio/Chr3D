#!/usr/bin/env python3
# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
# This software was developed with support from the National Science Foundation under CAREER Award DBI-2239350.
"""
System Information Utility for Chr3D

Collects comprehensive system information including OS, CPU, memory, GPU,
and saves it to a file for reproducibility and debugging purposes.
"""

import platform
import subprocess
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


def run_command(cmd: str, timeout: int = 5) -> str:
    """Execute shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except Exception:
        return "N/A"


def get_size(bytes_val: float, suffix: str = "B") -> str:
    """Convert bytes to human readable format."""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes_val < factor:
            return f"{bytes_val:.2f} {unit}{suffix}"
        bytes_val /= factor
    return f"{bytes_val:.2f} P{suffix}"


def get_system_info() -> Dict[str, Any]:
    """
    Collect comprehensive system information.
    
    Returns:
        Dictionary containing all system information
    """
    info = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'os': {},
        'cpu': {},
        'memory': {},
        'gpu': {},
        'python': {},
    }
    
    # OS Information
    uname = platform.uname()
    info['os'] = {
        'system': uname.system,
        'node_name': uname.node,
        'release': uname.release,
        'version': uname.version,
        'machine': uname.machine,
        'processor': uname.processor,
        'platform': platform.platform(),
        'architecture': platform.architecture()[0],
    }
    
    # Linux distribution info
    distro_info = run_command("cat /etc/os-release 2>/dev/null | grep -E '^(NAME|VERSION|ID)=' | head -5")
    if distro_info != "N/A":
        info['os']['distribution'] = distro_info
    
    info['os']['kernel_version'] = run_command("uname -r")
    
    # CPU Information
    try:
        import psutil
        info['cpu']['physical_cores'] = psutil.cpu_count(logical=False)
        info['cpu']['total_cores'] = psutil.cpu_count(logical=True)
        
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            info['cpu']['frequency_current_mhz'] = round(cpu_freq.current, 2)
            info['cpu']['frequency_min_mhz'] = round(cpu_freq.min, 2)
            info['cpu']['frequency_max_mhz'] = round(cpu_freq.max, 2)
        
        info['cpu']['usage_percent'] = psutil.cpu_percent(interval=0.1)
    except ImportError:
        info['cpu']['physical_cores'] = int(run_command("nproc") or 1)
        info['cpu']['total_cores'] = int(run_command("nproc") or 1)
    
    # CPU model
    cpu_model = run_command("cat /proc/cpuinfo | grep 'model name' | uniq | cut -d':' -f2")
    if cpu_model != "N/A":
        info['cpu']['model'] = cpu_model.strip()
    
    # CPU vendor and cache
    info['cpu']['vendor'] = run_command("lscpu | grep 'Vendor ID' | cut -d':' -f2").strip()
    info['cpu']['cache_l1d'] = run_command("lscpu | grep 'L1d cache' | cut -d':' -f2").strip()
    info['cpu']['cache_l1i'] = run_command("lscpu | grep 'L1i cache' | cut -d':' -f2").strip()
    info['cpu']['cache_l2'] = run_command("lscpu | grep 'L2 cache' | cut -d':' -f2").strip()
    info['cpu']['cache_l3'] = run_command("lscpu | grep 'L3 cache' | cut -d':' -f2").strip()
    
    # Memory Information
    try:
        import psutil
        svmem = psutil.virtual_memory()
        info['memory']['total'] = get_size(svmem.total)
        info['memory']['total_bytes'] = svmem.total
        info['memory']['available'] = get_size(svmem.available)
        info['memory']['available_bytes'] = svmem.available
        info['memory']['used'] = get_size(svmem.used)
        info['memory']['used_percent'] = svmem.percent
        info['memory']['free'] = get_size(svmem.free)
        
        swap = psutil.swap_memory()
        info['memory']['swap_total'] = get_size(swap.total)
        info['memory']['swap_used'] = get_size(swap.used)
        info['memory']['swap_percent'] = swap.percent
    except ImportError:
        meminfo = run_command("cat /proc/meminfo | grep MemTotal | awk '{print $2}'")
        if meminfo != "N/A":
            info['memory']['total_kb'] = int(meminfo)
            info['memory']['total'] = get_size(int(meminfo) * 1024)
    
    # GPU Information
    nvidia_smi = run_command("nvidia-smi --query-gpu=index,name,driver_version,memory.total,memory.free,memory.used,temperature.gpu,compute_cap --format=csv,noheader 2>/dev/null")
    if nvidia_smi != "N/A" and len(nvidia_smi) > 10 and "failed" not in nvidia_smi.lower():
        info['gpu']['nvidia_available'] = True
        info['gpu']['gpus'] = []
        for gpu in nvidia_smi.split('\n'):
            if gpu.strip():
                parts = [p.strip() for p in gpu.split(',')]
                if len(parts) >= 4:
                    gpu_info = {
                        'index': parts[0],
                        'name': parts[1],
                        'driver_version': parts[2],
                        'memory_total': parts[3],
                    }
                    if len(parts) > 4:
                        gpu_info['memory_free'] = parts[4]
                    if len(parts) > 5:
                        gpu_info['memory_used'] = parts[5]
                    if len(parts) > 6:
                        gpu_info['temperature'] = parts[6]
                    if len(parts) > 7:
                        gpu_info['compute_capability'] = parts[7]
                    info['gpu']['gpus'].append(gpu_info)
    else:
        info['gpu']['nvidia_available'] = False
        info['gpu']['status'] = run_command("nvidia-smi 2>&1 | head -3")
    
    # All display devices
    all_gpus = run_command("lspci | grep -iE 'vga|3d|display'")
    if all_gpus != "N/A":
        info['gpu']['display_devices'] = all_gpus.split('\n')
    
    # Python Information
    info['python']['version'] = platform.python_version()
    info['python']['implementation'] = platform.python_implementation()
    info['python']['compiler'] = platform.python_compiler()
    
    # Check for key packages
    packages = ['numpy', 'pandas', 'pysam', 'cooler', 'psutil']
    info['python']['packages'] = {}
    for pkg in packages:
        try:
            mod = __import__(pkg)
            info['python']['packages'][pkg] = getattr(mod, '__version__', 'installed')
        except ImportError:
            info['python']['packages'][pkg] = 'not installed'
    
    return info


def format_system_info(info: Dict[str, Any]) -> str:
    """
    Format system information as a readable string.
    
    Args:
        info: Dictionary from get_system_info()
        
    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("SYSTEM CONFIGURATION")
    lines.append("=" * 80)
    lines.append(f"Scan Date: {info['timestamp']}")
    lines.append("=" * 80)
    
    # OS Information
    lines.append("\n" + "-" * 80)
    lines.append("OPERATING SYSTEM")
    lines.append("-" * 80)
    os_info = info.get('os', {})
    lines.append(f"System: {os_info.get('system', 'N/A')}")
    lines.append(f"Node Name: {os_info.get('node_name', 'N/A')}")
    lines.append(f"Release: {os_info.get('release', 'N/A')}")
    lines.append(f"Version: {os_info.get('version', 'N/A')}")
    lines.append(f"Machine: {os_info.get('machine', 'N/A')}")
    lines.append(f"Platform: {os_info.get('platform', 'N/A')}")
    lines.append(f"Architecture: {os_info.get('architecture', 'N/A')}")
    lines.append(f"Kernel Version: {os_info.get('kernel_version', 'N/A')}")
    if 'distribution' in os_info:
        lines.append(f"Distribution:\n  {os_info['distribution'].replace(chr(10), chr(10) + '  ')}")
    
    # CPU Information
    lines.append("\n" + "-" * 80)
    lines.append("CPU INFORMATION")
    lines.append("-" * 80)
    cpu_info = info.get('cpu', {})
    lines.append(f"Model: {cpu_info.get('model', 'N/A')}")
    lines.append(f"Vendor: {cpu_info.get('vendor', 'N/A')}")
    lines.append(f"Physical Cores: {cpu_info.get('physical_cores', 'N/A')}")
    lines.append(f"Total Cores (with HT): {cpu_info.get('total_cores', 'N/A')}")
    if 'frequency_current_mhz' in cpu_info:
        lines.append(f"Frequency: {cpu_info.get('frequency_current_mhz', 'N/A')} MHz (current)")
        lines.append(f"           {cpu_info.get('frequency_min_mhz', 'N/A')} - {cpu_info.get('frequency_max_mhz', 'N/A')} MHz (range)")
    lines.append(f"L1d Cache: {cpu_info.get('cache_l1d', 'N/A')}")
    lines.append(f"L1i Cache: {cpu_info.get('cache_l1i', 'N/A')}")
    lines.append(f"L2 Cache: {cpu_info.get('cache_l2', 'N/A')}")
    lines.append(f"L3 Cache: {cpu_info.get('cache_l3', 'N/A')}")
    
    # Memory Information
    lines.append("\n" + "-" * 80)
    lines.append("MEMORY INFORMATION")
    lines.append("-" * 80)
    mem_info = info.get('memory', {})
    lines.append(f"Total RAM: {mem_info.get('total', 'N/A')}")
    lines.append(f"Available: {mem_info.get('available', 'N/A')}")
    lines.append(f"Used: {mem_info.get('used', 'N/A')} ({mem_info.get('used_percent', 'N/A')}%)")
    lines.append(f"Free: {mem_info.get('free', 'N/A')}")
    lines.append(f"Swap Total: {mem_info.get('swap_total', 'N/A')}")
    lines.append(f"Swap Used: {mem_info.get('swap_used', 'N/A')} ({mem_info.get('swap_percent', 'N/A')}%)")
    
    # GPU Information
    lines.append("\n" + "-" * 80)
    lines.append("GPU INFORMATION")
    lines.append("-" * 80)
    gpu_info = info.get('gpu', {})
    if gpu_info.get('nvidia_available'):
        for gpu in gpu_info.get('gpus', []):
            lines.append(f"GPU {gpu.get('index', 'N/A')}:")
            lines.append(f"  Model: {gpu.get('name', 'N/A')}")
            lines.append(f"  Driver: {gpu.get('driver_version', 'N/A')}")
            lines.append(f"  Memory Total: {gpu.get('memory_total', 'N/A')}")
            lines.append(f"  Memory Free: {gpu.get('memory_free', 'N/A')}")
            lines.append(f"  Memory Used: {gpu.get('memory_used', 'N/A')}")
            lines.append(f"  Temperature: {gpu.get('temperature', 'N/A')}")
            lines.append(f"  Compute Capability: {gpu.get('compute_capability', 'N/A')}")
    else:
        lines.append(f"NVIDIA GPU: Not available")
        lines.append(f"Status: {gpu_info.get('status', 'N/A')}")
    
    if 'display_devices' in gpu_info:
        lines.append("\nAll Display Devices:")
        for dev in gpu_info['display_devices']:
            if dev.strip():
                lines.append(f"  {dev}")
    
    # Python Information
    lines.append("\n" + "-" * 80)
    lines.append("PYTHON ENVIRONMENT")
    lines.append("-" * 80)
    py_info = info.get('python', {})
    lines.append(f"Python Version: {py_info.get('version', 'N/A')}")
    lines.append(f"Implementation: {py_info.get('implementation', 'N/A')}")
    lines.append(f"Compiler: {py_info.get('compiler', 'N/A')}")
    lines.append("\nKey Packages:")
    for pkg, ver in py_info.get('packages', {}).items():
        lines.append(f"  {pkg}: {ver}")
    
    lines.append("\n" + "=" * 80)
    lines.append("END OF SYSTEM CONFIGURATION")
    lines.append("=" * 80)
    
    return '\n'.join(lines)


def save_system_info(output_path: str) -> str:
    """
    Collect and save system information to a file.
    
    Args:
        output_path: Path to save the system info file
        
    Returns:
        Path to the saved file
    """
    info = get_system_info()
    formatted = format_system_info(info)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(formatted)
    
    return str(output_path)


def print_system_info():
    """Print system information to stdout."""
    info = get_system_info()
    print(format_system_info(info))


if __name__ == "__main__":
    print_system_info()
