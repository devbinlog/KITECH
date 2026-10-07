#!/usr/bin/env python
"""
Basic Usage Example - STEP PMI Reader

Demonstrates fundamental operations:
- Loading a STEP file
- Extracting PMI data
- Accessing datums, tolerances, and annotations
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from step_pmi_reader_agent import StepPmiReaderAgent


def main():
    # Initialize agent
    agent = StepPmiReaderAgent()
    print(f"Agent: {agent.name}")
    print("=" * 50)

    # Process sample file
    sample_file = Path(__file__).parent.parent / "samples" / "sample_ap242_pmi.stp"
    result = agent.process(str(sample_file))

    if result["status"] != "success":
        print(f"Error: {result['message']}")
        return

    data = result["data"]

    # Display summary
    print(f"\nFile: {data['file_name']}")
    print(f"Schema: {data['schema']}")
    print(f"\nSummary:")
    for key, value in data["summary"].items():
        print(f"  {key}: {value}")

    # Display datums
    print(f"\n--- Datums ({len(data['datums'])}) ---")
    for datum in data["datums"]:
        print(f"  {datum['id']}: Datum {datum['label']}")

    # Display geometric tolerances
    print(f"\n--- Geometric Tolerances ({len(data['geometric_tolerances'])}) ---")
    for tol in data["geometric_tolerances"][:5]:  # First 5
        refs = ", ".join(tol["datum_references"]) if tol["datum_references"] else "none"
        print(f"  {tol['id']}: {tol['tolerance_type']} = {tol['tolerance_value']} {tol['unit']} (refs: {refs})")
    if len(data["geometric_tolerances"]) > 5:
        print(f"  ... and {len(data['geometric_tolerances']) - 5} more")

    # Display dimensional tolerances
    print(f"\n--- Dimensional Tolerances ({len(data['dimensional_tolerances'])}) ---")
    for dim in data["dimensional_tolerances"][:5]:  # First 5
        limits = ""
        if dim["upper_limit"] is not None:
            limits = f" (+{dim['upper_limit']}/{dim['lower_limit']})"
        print(f"  {dim['id']}: {dim['dimension_type']} = {dim['nominal_value']}{limits} {dim['unit']}")
    if len(data["dimensional_tolerances"]) > 5:
        print(f"  ... and {len(data['dimensional_tolerances']) - 5} more")

    # Display surface finishes
    print(f"\n--- Surface Finishes ({len(data['surface_finishes'])}) ---")
    for sf in data["surface_finishes"]:
        method = f" ({sf['method']})" if sf.get("method") else ""
        print(f"  {sf['id']}: Ra {sf['roughness_value']} {sf['unit']}{method}")

    # Display annotations
    print(f"\n--- Annotations ({len(data['annotations'])}) ---")
    for ann in data["annotations"][:3]:  # First 3
        print(f"  {ann['id']}: {ann['type']}")
    if len(data["annotations"]) > 3:
        print(f"  ... and {len(data['annotations']) - 3} more")


if __name__ == "__main__":
    main()
