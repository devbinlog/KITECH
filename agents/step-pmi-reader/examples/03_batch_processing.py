#!/usr/bin/env python
"""
Batch Processing Example - STEP PMI Reader

Demonstrates processing multiple STEP files:
- Directory scanning
- Parallel processing
- Aggregated results
- Error handling
"""

import sys
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from step_pmi_reader_agent import StepPmiReaderAgent

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single file"""
    file_path: str
    success: bool
    datum_count: int = 0
    gdt_count: int = 0
    dim_count: int = 0
    surface_count: int = 0
    error: Optional[str] = None


def process_single_file(agent: StepPmiReaderAgent, file_path: Path) -> ProcessingResult:
    """Process a single STEP file and return result summary"""
    try:
        result = agent.process(str(file_path))
        if result["status"] == "success":
            data = result["data"]
            return ProcessingResult(
                file_path=str(file_path),
                success=True,
                datum_count=data["summary"]["datum_count"],
                gdt_count=data["summary"]["geometric_tolerance_count"],
                dim_count=data["summary"]["dimensional_tolerance_count"],
                surface_count=data["summary"]["surface_finish_count"],
            )
        else:
            return ProcessingResult(
                file_path=str(file_path),
                success=False,
                error=result.get("message", "Unknown error"),
            )
    except Exception as e:
        return ProcessingResult(
            file_path=str(file_path),
            success=False,
            error=str(e),
        )


def batch_process_directory(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    pattern: str = "*.stp",
    max_workers: int = 4,
) -> List[ProcessingResult]:
    """
    Process all STEP files in a directory.
    
    Args:
        input_dir: Directory containing STEP files
        output_dir: Optional directory for JSON outputs
        pattern: Glob pattern for files (default: *.stp)
        max_workers: Number of parallel workers
    
    Returns:
        List of ProcessingResult objects
    """
    agent = StepPmiReaderAgent()
    files = list(input_dir.glob(pattern))
    
    # Also check for .step extension
    files.extend(input_dir.glob(pattern.replace(".stp", ".step")))
    files = list(set(files))  # Remove duplicates
    
    if not files:
        logger.warning(f"No files matching '{pattern}' found in {input_dir}")
        return []
    
    logger.info(f"Found {len(files)} files to process")
    
    results: List[ProcessingResult] = []
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_single_file, agent, f): f 
            for f in files
        }
        
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                status = "✓" if result.success else "✗"
                logger.info(f"  {status} {file_path.name}")
            except Exception as e:
                results.append(ProcessingResult(
                    file_path=str(file_path),
                    success=False,
                    error=str(e),
                ))
                logger.info(f"  ✗ {file_path.name}: {e}")
    
    # Save individual JSON files if output_dir specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        for file_path in files:
            result = agent.process(str(file_path))
            if result["status"] == "success":
                output_file = output_dir / f"{file_path.stem}_pmi.json"
                with open(output_file, "w") as f:
                    json.dump(result["data"], f, indent=2)
    
    return results


def print_summary(results: List[ProcessingResult]):
    """Print batch processing summary"""
    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)
    
    total = len(results)
    success = sum(1 for r in results if r.success)
    failed = total - success
    
    print(f"\nFiles processed: {total}")
    print(f"  Successful: {success}")
    print(f"  Failed: {failed}")
    
    if success > 0:
        total_datums = sum(r.datum_count for r in results if r.success)
        total_gdt = sum(r.gdt_count for r in results if r.success)
        total_dims = sum(r.dim_count for r in results if r.success)
        total_surfaces = sum(r.surface_count for r in results if r.success)
        
        print(f"\nPMI Totals:")
        print(f"  Datums: {total_datums}")
        print(f"  Geometric Tolerances: {total_gdt}")
        print(f"  Dimensional Tolerances: {total_dims}")
        print(f"  Surface Finishes: {total_surfaces}")
        
        print(f"\nAverages per file:")
        print(f"  Datums: {total_datums / success:.1f}")
        print(f"  Geometric Tolerances: {total_gdt / success:.1f}")
        print(f"  Dimensional Tolerances: {total_dims / success:.1f}")
        print(f"  Surface Finishes: {total_surfaces / success:.1f}")
    
    if failed > 0:
        print(f"\nFailed files:")
        for r in results:
            if not r.success:
                print(f"  - {Path(r.file_path).name}: {r.error}")


def main():
    # Example: Process sample directory
    samples_dir = Path(__file__).parent.parent / "samples"
    output_dir = Path(__file__).parent / "output" / "batch"
    
    print("STEP PMI Batch Processor")
    print(f"Input directory: {samples_dir}")
    print(f"Output directory: {output_dir}")
    print("-" * 60)
    
    results = batch_process_directory(
        input_dir=samples_dir,
        output_dir=output_dir,
        pattern="*.stp",
        max_workers=4,
    )
    
    print_summary(results)
    
    # Save summary report
    report_file = output_dir / "batch_report.json"
    report = {
        "total_files": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "files": [
            {
                "file": Path(r.file_path).name,
                "success": r.success,
                "datums": r.datum_count,
                "gdt": r.gdt_count,
                "dimensions": r.dim_count,
                "surfaces": r.surface_count,
                "error": r.error,
            }
            for r in results
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    main()
