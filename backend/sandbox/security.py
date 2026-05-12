"""
Sandbox security configuration.
"""

# Docker security settings
SANDBOX_CONFIG = {
    # Network disabled - no network access
    "network_disabled": True,

    # Memory limit (256MB default)
    "mem_limit": "256m",

    # Process limit (prevent fork bombs)
    "pids_limit": 50,

    # CPU limit (50% of one core)
    "cpu_period": 100000,
    "cpu_quota": 50000,

    # Read-only filesystem with tmpfs for /tmp
    "read_only": True,
    "tmpfs": ["/tmp"],

    # Security options
    "security_opt": ["no-new-privileges:true"],

    # Remove container after execution
    "auto_remove": True,
}

# Commands that should be blocked
BLOCKED_COMMANDS = [
    "rm",
    "rmdir",
    "mkfs",
    "dd",
    "fdisk",
    "sfdisk",
    "parted",
    "mount",
    "umount",
    "chroot",
    "pivot_root",
    "exec",
    "systemctl",
    "service",
    "init",
]

# Dangerous system calls to monitor
DANGEROUS_SYSCALLS = [
    "fork",
    "clone",
    "execve",
    "kill",
    "ptrace",
    "setuid",
    "setgid",
    "setreuid",
    "setregid",
    "setresuid",
    "setresgid",
    "capset",
    "syslog",
    "adjtimex",
    "settimeofday",
    "mount",
    "umount2",
    "swapon",
    "swapoff",
    "reboot",
    "setns",
    "unshare",
]


def get_container_config(language: str, time_limit: int = 1000, memory_limit: int = 256) -> dict:
    """
    Get container configuration for a specific language.

    Args:
        language: Programming language
        time_limit: Time limit in milliseconds
        memory_limit: Memory limit in MB

    Returns:
        Dict with container configuration
    """
    config = SANDBOX_CONFIG.copy()

    # Adjust memory limit based on language
    if language == "java":
        config["mem_limit"] = "512m"  # Java needs more memory

    # Set time limit
    config["cpu_quota"] = int(time_limit * 50)  # Convert ms to CPU quota

    return config
