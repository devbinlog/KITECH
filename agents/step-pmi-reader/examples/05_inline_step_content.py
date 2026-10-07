#!/usr/bin/env python
"""
Inline STEP Content Example - STEP PMI Reader

Demonstrates processing STEP content directly as a string,
useful for:
- API integrations
- Stream processing
- Unit testing
- Database stored content
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from step_pmi_reader_agent import StepPmiReaderAgent


# Sample inline STEP content with PMI
INLINE_STEP_CONTENT = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Inline PMI Example'),'2;1');
FILE_NAME('inline_example.stp','2026-01-01T00:00:00',('Test'),('Test'),'','','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
/* Minimal geometry */
#1 = PRODUCT('InlinePart','Test Part','',(#2));
#2 = PRODUCT_CONTEXT('',#3,'mechanical');
#3 = APPLICATION_CONTEXT('automotive design');

/* Datums */
#10 = DATUM('Datum A','A');
#11 = DATUM('Datum B','B');

/* Geometric Tolerances */
#20 = POSITION_TOLERANCE('Hole Position',0.05,#10,#11);
#21 = FLATNESS_TOLERANCE('Top Face',0.02);
#22 = PERPENDICULARITY_TOLERANCE('Side Face',0.03,#10);

/* Dimensional Tolerances */
#30 = LINEAR_DIMENSION('Length',100.0,0.1,-0.1);
#31 = DIAMETER_DIMENSION('Hole',10.0,0.02,0.0);

/* Surface Finish */
#40 = SURFACE_ROUGHNESS('Machined',1.6);

ENDSEC;
END-ISO-10303-21;
"""


def main():
    agent = StepPmiReaderAgent()

    print("=" * 60)
    print("Processing Inline STEP Content")
    print("=" * 60)

    # Process inline content
    result = agent.process(INLINE_STEP_CONTENT)

    if result["status"] == "success":
        data = result["data"]

        print(f"\nFile: {data['file_name']}")
        print(f"Schema: {data['schema']}")

        print("\nExtracted PMI:")
        print(f"  Datums: {len(data['datums'])}")
        for d in data["datums"]:
            print(f"    - {d['label']}")

        print(f"  Geometric Tolerances: {len(data['geometric_tolerances'])}")
        for t in data["geometric_tolerances"]:
            print(f"    - {t['tolerance_type']}: {t['tolerance_value']}mm")

        print(f"  Dimensional Tolerances: {len(data['dimensional_tolerances'])}")
        for d in data["dimensional_tolerances"]:
            print(f"    - {d['dimension_type']}: {d['nominal_value']}mm")

        print(f"  Surface Finishes: {len(data['surface_finishes'])}")
        for s in data["surface_finishes"]:
            print(f"    - Ra {s['roughness_value']}μm")
    else:
        print(f"Error: {result['message']}")

    # Demo: Get PMIData object directly
    print("\n" + "-" * 60)
    print("Using get_pmi_data() for programmatic access:")

    pmi = agent.get_pmi_data(INLINE_STEP_CONTENT)
    if pmi:
        print(f"  Datums: {[d.label for d in pmi.datums]}")
        print(f"  GD&T types: {[t.tolerance_type for t in pmi.geometric_tolerances]}")

        # Convert to JSON string
        json_str = pmi.to_json(indent=2)
        print(f"\n  JSON output length: {len(json_str)} chars")

    # Demo: Minimal content (no PMI)
    print("\n" + "-" * 60)
    print("Processing minimal STEP (no PMI):")

    minimal_step = """ISO-10303-21;
HEADER;
FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));
ENDSEC;
DATA;
#1 = PRODUCT('Simple','Simple Part','',(#2));
ENDSEC;
END-ISO-10303-21;
"""

    result = agent.process(minimal_step)
    if result["status"] == "success":
        data = result["data"]
        print(f"  Schema detected: {data['schema']}")
        print(f"  Datums: {len(data['datums'])}")
        print(f"  GD&T: {len(data['geometric_tolerances'])}")
        print("  (AP203 schema has no PMI support)")


if __name__ == "__main__":
    main()
