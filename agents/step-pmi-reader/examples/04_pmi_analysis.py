#!/usr/bin/env python
"""
PMI Analysis Example - STEP PMI Reader

Demonstrates advanced PMI analysis:
- Tolerance stack-up analysis
- GD&T validation checks
- Datum reference frame analysis
- Manufacturing feasibility assessment
"""

import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from step_pmi_reader_agent import StepPmiReaderAgent, PMIData


class PMIAnalyzer:
    """Analyze PMI data for manufacturing and quality insights"""

    # Typical tolerance grades (ISO 2768)
    TOLERANCE_GRADES = {
        "fine": {"linear": 0.05, "angular": 0.5},
        "medium": {"linear": 0.1, "angular": 1.0},
        "coarse": {"linear": 0.3, "angular": 2.0},
        "very_coarse": {"linear": 0.5, "angular": 3.0},
    }

    # Typical surface finish requirements by process
    SURFACE_FINISH_PROCESSES = {
        "grinding": (0.2, 0.8),      # Ra range in μm
        "turning": (0.8, 3.2),
        "milling": (1.6, 6.3),
        "drilling": (3.2, 12.5),
        "casting": (6.3, 25.0),
    }

    def __init__(self, pmi_data: PMIData):
        self.pmi = pmi_data

    def analyze(self) -> Dict[str, Any]:
        """Run complete PMI analysis"""
        return {
            "file": self.pmi.file_name,
            "schema": self.pmi.schema,
            "datum_analysis": self.analyze_datum_system(),
            "gdt_analysis": self.analyze_geometric_tolerances(),
            "dimensional_analysis": self.analyze_dimensional_tolerances(),
            "surface_analysis": self.analyze_surface_requirements(),
            "manufacturing_assessment": self.assess_manufacturability(),
            "recommendations": self.generate_recommendations(),
        }

    def analyze_datum_system(self) -> Dict[str, Any]:
        """Analyze datum reference frame"""
        datums = self.pmi.datums
        labels = [d.label for d in datums]

        analysis = {
            "count": len(datums),
            "labels": labels,
            "has_abc": all(x in labels for x in ["A", "B", "C"]),
            "issues": [],
        }

        # Check for proper datum hierarchy
        if len(datums) > 0:
            if "A" not in labels:
                analysis["issues"].append("Missing primary datum (A)")
            if len(datums) >= 2 and "B" not in labels:
                analysis["issues"].append("Missing secondary datum (B)")
            if len(datums) >= 3 and "C" not in labels:
                analysis["issues"].append("Missing tertiary datum (C)")

        # Check for duplicate labels
        label_counts = Counter(labels)
        duplicates = [l for l, c in label_counts.items() if c > 1]
        if duplicates:
            analysis["issues"].append(f"Duplicate datum labels: {duplicates}")

        return analysis

    def analyze_geometric_tolerances(self) -> Dict[str, Any]:
        """Analyze GD&T specifications"""
        gdt = self.pmi.geometric_tolerances

        # Group by type
        by_type = defaultdict(list)
        for tol in gdt:
            by_type[tol.tolerance_type].append(tol.tolerance_value)

        # Statistics
        type_stats = {}
        for tol_type, values in by_type.items():
            type_stats[tol_type] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

        # Find tightest tolerances
        all_values = [(t.tolerance_type, t.tolerance_value, t.id) for t in gdt]
        tightest = sorted(all_values, key=lambda x: x[1])[:5]

        # Datum references usage
        datum_usage = Counter()
        for tol in gdt:
            for ref in tol.datum_references:
                datum_usage[ref] += 1

        return {
            "count": len(gdt),
            "by_type": type_stats,
            "tightest_tolerances": [
                {"type": t, "value": v, "id": i} for t, v, i in tightest
            ],
            "datum_usage": dict(datum_usage),
            "issues": self._check_gdt_issues(gdt),
        }

    def _check_gdt_issues(self, gdt: List) -> List[str]:
        """Check for potential GD&T issues"""
        issues = []

        for tol in gdt:
            # Position tolerance without datum reference
            if tol.tolerance_type == "POSITION" and not tol.datum_references:
                issues.append(f"{tol.id}: Position tolerance without datum reference")

            # Very tight tolerances
            if tol.tolerance_value < 0.005:
                issues.append(
                    f"{tol.id}: Very tight tolerance ({tol.tolerance_value}mm) - "
                    "may require special equipment"
                )

        return issues

    def analyze_dimensional_tolerances(self) -> Dict[str, Any]:
        """Analyze dimensional tolerances"""
        dims = self.pmi.dimensional_tolerances

        # Tolerance ranges
        tolerance_ranges = []
        for dim in dims:
            if dim.upper_limit is not None and dim.lower_limit is not None:
                total_range = dim.upper_limit - dim.lower_limit
                tolerance_ranges.append({
                    "id": dim.id,
                    "type": dim.dimension_type,
                    "nominal": dim.nominal_value,
                    "range": total_range,
                    "symmetric": abs(dim.upper_limit + dim.lower_limit) < 0.001,
                })

        # Classify tolerance grades
        grades = {"fine": 0, "medium": 0, "coarse": 0, "very_coarse": 0}
        for tr in tolerance_ranges:
            if tr["range"] <= 0.1:
                grades["fine"] += 1
            elif tr["range"] <= 0.2:
                grades["medium"] += 1
            elif tr["range"] <= 0.6:
                grades["coarse"] += 1
            else:
                grades["very_coarse"] += 1

        return {
            "count": len(dims),
            "by_type": dict(Counter(d.dimension_type for d in dims)),
            "tolerance_grades": grades,
            "tightest": sorted(tolerance_ranges, key=lambda x: x.get("range", 999))[:3],
        }

    def analyze_surface_requirements(self) -> Dict[str, Any]:
        """Analyze surface finish requirements"""
        surfaces = self.pmi.surface_finishes

        if not surfaces:
            return {"count": 0, "recommended_processes": []}

        ra_values = [s.roughness_value for s in surfaces]

        # Determine required processes
        processes = set()
        for ra in ra_values:
            for process, (min_ra, max_ra) in self.SURFACE_FINISH_PROCESSES.items():
                if min_ra <= ra <= max_ra:
                    processes.add(process)
                    break

        # Find tightest requirement
        min_ra = min(ra_values)
        required_process = "unknown"
        for process, (min_p, max_p) in sorted(
            self.SURFACE_FINISH_PROCESSES.items(), key=lambda x: x[1][0]
        ):
            if min_ra <= max_p:
                required_process = process
                break

        return {
            "count": len(surfaces),
            "min_ra": min_ra,
            "max_ra": max(ra_values),
            "avg_ra": sum(ra_values) / len(ra_values),
            "recommended_processes": list(processes),
            "tightest_requires": required_process,
        }

    def assess_manufacturability(self) -> Dict[str, Any]:
        """Assess overall manufacturing difficulty"""
        gdt = self.pmi.geometric_tolerances
        dims = self.pmi.dimensional_tolerances
        surfaces = self.pmi.surface_finishes

        # Scoring factors
        score = 100  # Start with perfect score

        # Tight geometric tolerances
        tight_gdt = sum(1 for t in gdt if t.tolerance_value < 0.01)
        score -= tight_gdt * 5

        # Very tight dimensional tolerances
        for d in dims:
            if d.upper_limit and d.lower_limit:
                range_val = d.upper_limit - d.lower_limit
                if range_val < 0.05:
                    score -= 10
                elif range_val < 0.1:
                    score -= 5

        # Fine surface finish
        for s in surfaces:
            if s.roughness_value < 0.8:
                score -= 10  # Requires grinding
            elif s.roughness_value < 1.6:
                score -= 5   # Requires fine machining

        # Complexity (many features)
        total_features = len(gdt) + len(dims) + len(surfaces)
        if total_features > 30:
            score -= 10
        elif total_features > 20:
            score -= 5

        # Clamp score
        score = max(0, min(100, score))

        # Determine difficulty level
        if score >= 80:
            difficulty = "Easy"
        elif score >= 60:
            difficulty = "Moderate"
        elif score >= 40:
            difficulty = "Challenging"
        else:
            difficulty = "Difficult"

        return {
            "score": score,
            "difficulty": difficulty,
            "factors": {
                "tight_geometric_tolerances": tight_gdt,
                "total_features": total_features,
                "fine_surface_count": sum(1 for s in surfaces if s.roughness_value < 1.6),
            },
        }

    def generate_recommendations(self) -> List[str]:
        """Generate manufacturing recommendations"""
        recs = []

        # Based on analysis
        surfaces = self.pmi.surface_finishes
        gdt = self.pmi.geometric_tolerances

        # Surface finish recommendations
        min_ra = min((s.roughness_value for s in surfaces), default=999)
        if min_ra < 0.8:
            recs.append("Consider grinding for fine surface finish (Ra < 0.8μm)")
        elif min_ra < 1.6:
            recs.append("Use fine turning/milling for surface finish requirements")

        # GD&T recommendations
        tight_positions = [t for t in gdt if t.tolerance_type == "POSITION" and t.tolerance_value < 0.02]
        if tight_positions:
            recs.append("Tight position tolerances require precision fixtures")

        # Datum recommendations
        if len(self.pmi.datums) < 3:
            recs.append("Consider adding complete datum reference frame (A, B, C)")

        # General recommendations
        if len(gdt) > 20:
            recs.append("Complex GD&T - consider CMM inspection")

        if not recs:
            recs.append("Standard machining processes should be sufficient")

        return recs


def main():
    agent = StepPmiReaderAgent()
    sample_file = Path(__file__).parent.parent / "samples" / "sample_ap242_pmi.stp"

    print("=" * 70)
    print("PMI ANALYSIS REPORT")
    print("=" * 70)

    # Get PMI data
    pmi_data = agent.get_pmi_data(str(sample_file))
    if not pmi_data:
        print("Failed to load PMI data")
        return

    # Run analysis
    analyzer = PMIAnalyzer(pmi_data)
    report = analyzer.analyze()

    # Print report
    print(f"\nFile: {report['file']}")
    print(f"Schema: {report['schema']}")

    # Datum Analysis
    da = report["datum_analysis"]
    print(f"\n--- DATUM SYSTEM ---")
    print(f"Datums: {da['count']} ({', '.join(da['labels'])})")
    print(f"Complete A-B-C: {'Yes' if da['has_abc'] else 'No'}")
    if da["issues"]:
        print("Issues:")
        for issue in da["issues"]:
            print(f"  ⚠ {issue}")

    # GD&T Analysis
    ga = report["gdt_analysis"]
    print(f"\n--- GEOMETRIC TOLERANCES ---")
    print(f"Total: {ga['count']}")
    print("By type:")
    for ttype, stats in ga["by_type"].items():
        print(f"  {ttype}: {stats['count']} (min={stats['min']}, max={stats['max']})")
    print("Tightest tolerances:")
    for t in ga["tightest_tolerances"][:3]:
        print(f"  {t['id']}: {t['type']} = {t['value']}mm")
    if ga["issues"]:
        print("Issues:")
        for issue in ga["issues"]:
            print(f"  ⚠ {issue}")

    # Dimensional Analysis
    dima = report["dimensional_analysis"]
    print(f"\n--- DIMENSIONAL TOLERANCES ---")
    print(f"Total: {dima['count']}")
    print(f"Grades: {dima['tolerance_grades']}")

    # Surface Analysis
    sa = report["surface_analysis"]
    print(f"\n--- SURFACE REQUIREMENTS ---")
    print(f"Specifications: {sa['count']}")
    if sa["count"] > 0:
        print(f"Ra range: {sa['min_ra']} - {sa['max_ra']} μm")
        print(f"Tightest requires: {sa['tightest_requires']}")

    # Manufacturing Assessment
    ma = report["manufacturing_assessment"]
    print(f"\n--- MANUFACTURABILITY ---")
    print(f"Score: {ma['score']}/100")
    print(f"Difficulty: {ma['difficulty']}")

    # Recommendations
    print(f"\n--- RECOMMENDATIONS ---")
    for rec in report["recommendations"]:
        print(f"  • {rec}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
