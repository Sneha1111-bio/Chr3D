# Copyright (c) 2026 Rudhra Joshi and Yong Chen
# Licensed under the MIT License. See LICENSE in the project root for details.
# This software was developed with support from the National Science Foundation under CAREER Award DBI-2239350.
"""
Chr3D Logging Module

Provides centralized logging configuration and utilities for the Chr3D pipeline.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Default log format
default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
default_datefmt = '%Y-%m-%d %H:%M:%S'


def setup_logging(verbose: bool = False, log_file: str = None, logger_name: str = 'chr3d'):
    """
    Configure logging based on verbosity and optional log file.
    
    Args:
        verbose: Enable DEBUG level logging if True, INFO otherwise
        log_file: Optional path to log file for file output
        logger_name: Name for the logger (default: 'chr3d')
    
    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        # Ensure directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format=default_format,
        datefmt=default_datefmt,
        handlers=handlers,
        force=True
    )
    
    logger = logging.getLogger(logger_name)
    logger.info(f"Logging initialized (level: {'DEBUG' if verbose else 'INFO'})")
    if log_file:
        logger.info(f"Log file: {log_file}")
    
    return logger


def get_logger(name: str = 'chr3d') -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


def log_section_header(logger: logging.Logger, title: str, width: int = 70):
    """Log a formatted section header."""
    logger.info("=" * width)
    logger.info(title)
    logger.info("=" * width)


def log_subsection(logger: logging.Logger, title: str, width: int = 70):
    """Log a formatted subsection header."""
    logger.info("\n" + "-" * width)
    logger.info(title)
    logger.info("-" * width)


def log_step_start(logger: logging.Logger, step_num: str, step_name: str, width: int = 70):
    """Log the start of a pipeline step."""
    logger.info("\n" + "=" * width)
    logger.info(f"STEP {step_num}: {step_name.upper()}")
    logger.info("=" * width)


def log_step_complete(logger: logging.Logger, step_name: str, duration: float = None):
    """Log the completion of a pipeline step."""
    if duration:
        logger.info(f"  {step_name} completed in: {duration:.1f}s")
    else:
        logger.info(f"  {step_name} complete")


def log_dict(logger: logging.Logger, data: dict, indent: int = 2):
    """Log a dictionary with formatted key-value pairs."""
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            logger.info(f"{prefix}{key}:")
            log_dict(logger, value, indent + 2)
        elif isinstance(value, float):
            logger.info(f"{prefix}{key}: {value:.4f}")
        elif isinstance(value, int):
            logger.info(f"{prefix}{key}: {value:,}")
        else:
            logger.info(f"{prefix}{key}: {value}")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m ({seconds:.0f}s)"
    else:
        hours = seconds / 3600
        minutes = (seconds % 3600) / 60
        return f"{hours:.1f}h ({int(hours)}h {int(minutes)}m)"


def create_qc_log_file(output_dir: str, sample_id: str, step_name: str, step_num: str) -> Path:
    """
    Create a QC log file path for a specific step.
    
    Args:
        output_dir: Base output directory
        sample_id: Sample identifier
        step_name: Name of the processing step
        step_num: Step number (e.g., '01', '02')
    
    Returns:
        Path object for the QC log file
    """
    qc_dir = Path(output_dir) / 'qc'
    qc_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = qc_dir / f'{sample_id}_{step_num}_{step_name}_qc.txt'
    return log_file


def write_qc_header(f, step_num: str, step_name: str, width: int = 50):
    """Write QC file header."""
    f.write(f"{'=' * width}\n")
    f.write(f"Step {step_num}: {step_name.upper()} QC\n")
    f.write(f"{'=' * width}\n")
    f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")


def write_qc_dict(f, data: dict, indent: int = 0):
    """Write dictionary to QC file with formatting."""
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            f.write(f"{prefix}{key}:\n")
            write_qc_dict(f, value, indent + 1)
        elif isinstance(value, float):
            f.write(f"{prefix}{key}: {value:.4f}\n")
        elif isinstance(value, int):
            f.write(f"{prefix}{key}: {value:,}\n")
        else:
            f.write(f"{prefix}{key}: {value}\n")


def write_qc_footer(f, width: int = 50):
    """Write QC file footer."""
    f.write(f"{'=' * width}\n")


# Initialize default logger on module import for backward compatibility
logger = logging.getLogger('chr3d')
logger.addHandler(logging.NullHandler())
