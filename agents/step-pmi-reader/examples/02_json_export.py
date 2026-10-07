#!/usr/bin/env python
"""
JSON Export Example - STEP PMI Reader

Demonstrates different ways to export PMI data to JSON:
1. Using process() with output_json parameter
2. Using extract_pmi_json() for file or string output
3. Using get_pmi_data() with PMIData methods
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from step_pmi_reader_agent import StepPmiReaderAgent


def main():
    agent = StepPmiReaderAgent()
    sample_file = Path(__file__).parent.parent / "samples" / "sample_ap242_pmi.stp"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("JSON Export Methods Demo")
    print("=" * 60)

    # Method 1: process() with output_json
    print("\n[Method 1] process() with output_json parameter")
    print("-" * 50)
    output_file1 = output_dir / "method1_output.json"
    result = agent.process(str(sample_file), output_json=str(output_file1))
    print(f"  Status: {result['status']}")
    print(f"  Saved to: {result.get('output_file', 'N/A')}")

    # Method 2a: extract_pmi_json() to file
    print("\n[Method 2a] extract_pmi_json() → File")
    print("-" * 50)
    output_file2 = output_dir / "method2_output.json"
    result = agent.extract_pmi_json(str(sample_file), output_path=str(output_file2))
    print(f"  Status: {result['status']}")
    print(f"  Saved to: {result.get('output_file', 'N/A')}")

    # Method 2b: extract_pmi_json() to string
    print("\n[Method 2b] extract_pmi_json() → JSON String")
    print("-" * 50)
    result = agent.extract_pmi_json(str(sample_file))
    json_str = result.get("json", "")
    print(f"  Status: {result['status']}")
    print(f"  JSON length: {len(json_str)} chars")
    print(f"  Preview (first 200 chars):\n{json_str[:200]}...")

    # Method 3: get_pmi_data() with PMIData methods
    print("\n[Method 3] get_pmi_data() + PMIData methods")
    print("-" * 50)
    pmi_data = agent.get_pmi_data(str(sample_file))
    if pmi_data:
        # Save with custom formatting
        output_file3 = output_dir / "method3_output.json"
        pmi_data.save_json(output_file3, indent=4)
        print(f"  Saved with indent=4 to: {output_file3}")

        # Get as dict for custom processing
        data_dict = pmi_data.to_dict()
        print(f"  Data dict keys: {list(data_dict.keys())}")

        # Custom JSON with specific fields
        custom_output = {
            "file": pmi_data.file_name,
            "schema": pmi_data.schema,
            "datums": [d.label for d in pmi_data.datums],
            "tolerance_count": len(pmi_data.geometric_tolerances),
        }
        custom_file = output_dir / "method3_custom.json"
        custom_file.write_text(json.dumps(custom_output, indent=2))
        print(f"  Custom output saved to: {custom_file}")

    # Summary
    print("\n" + "=" * 60)
    print("Output files created:")
    for f in sorted(output_dir.glob("*.json")):
        print(f"  - {f.name} ({f.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
