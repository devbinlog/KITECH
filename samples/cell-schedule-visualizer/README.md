# Cell Schedule Visualizer Samples

## 📋 Overview

Schedule visualization outputs and examples.

## 📁 Directory Structure

```
cell-schedule-visualizer/
├── output/                 # Generated dashboard files
│   └── schedule_dashboard.html  # Auto-generated visualization (created by orchestrator)
└── README.md (this file)
```

## 🎯 Dashboard Output

The `schedule_dashboard.html` file is automatically generated when running the orchestrator with a manufacturing workflow.

**Location**: `samples/cell-schedule-visualizer/output/schedule_dashboard.html`

**Contents**:
- Interactive Plotly-based visualization
- 6 key performance metrics
- Gantt chart with task timeline
- Machine utilization chart
- Work order lateness analysis
- Fully responsive design (mobile/tablet/desktop)

## 🚀 Usage

### Generate Dashboard via Orchestrator

```bash
# Run full manufacturing workflow (auto-generates dashboard)
uv run orchestrator_main.py \
  --workflow full-manufacturing \
  --input samples/simple/001_simple_square.nc
```

**Output**: `samples/cell-schedule-visualizer/output/schedule_dashboard.html`

### View Generated Dashboard

```bash
# Windows
start samples/cell-schedule-visualizer/output/schedule_dashboard.html

# macOS
open samples/cell-schedule-visualizer/output/schedule_dashboard.html

# Linux
xdg-open samples/cell-schedule-visualizer/output/schedule_dashboard.html
```

### Python API

```python
from agents.cell_schedule_visualizer.src import ScheduleVisualizerAgent

# Generate visualization from scheduling result
agent = ScheduleVisualizerAgent()
result = {
    "status": "success",
    "scheduled_tasks": [...],
    "statistics": {...},
    "quality_metrics": {...},
    "gantt_data": {...}
}

output = agent.process(result)
print(f"Dashboard: {output['html_path']}")
```

## 📊 Dashboard Visualization Components

### 1. Metrics Cards
**Key Performance Indicators**:
- 📊 **Total Tasks** - Number of scheduled tasks
- ⏱️ **Makespan** - Total schedule duration (hours)
- 📅 **Lateness** - Total hours delayed from due dates
- ⚙️ **Avg Utilization** - Average machine utilization (%)
- 🔧 **Machines** - Number of available machines
- ⏰ **Solve Time** - Optimization time (seconds)

### 2. Gantt Chart
**Task Timeline Visualization**:
- **X-axis**: Chronological timeline
- **Y-axis**: Machine assignments
- **Bars**: Individual tasks with details
- **Colors**: Task priority levels
- **Interactions**: Hover, zoom, pan

### 3. Machine Utilization Chart
**Efficiency Metrics**:
- Bar chart showing each machine's utilization %
- Identifies bottleneck machines
- Shows capacity analysis

### 4. Work Order Lateness Chart
**On-Time Performance**:
- Shows hours late for each work order
- Green = On time, Red = Late
- Total and per-work-order analysis

## 📈 Metrics Interpretation

### Excellent Performance
- ✅ Makespan: Minimal (goal: <10 hours)
- ✅ Lateness: 0 hours (all on-time)
- ✅ Utilization: 60-80% (efficient)
- ✅ Balanced load: No severe bottlenecks

### Needs Improvement
- ⚠️ High lateness: Check priorities and due dates
- ⚠️ Low utilization: Increase job volume
- ⚠️ Bottleneck: Load balance between machines
- ⚠️ All tasks failing: Check constraints

## 🎨 Customization

### Output Location
Dashboard generated to:
```
samples/cell-schedule-visualizer/output/schedule_dashboard.html
```

Configure in `agents/cell-schedule-visualizer/src/schedule_visualizer_agent.py`:
```python
output_dir = Path('.') / 'samples' / 'cell-schedule-visualizer' / 'output'
```

### Color Scheme
Edit `agents/cell-schedule-visualizer/config/visualizer_config.json`:
```json
{
  "colors": {
    "priority": {
      "high": "#FF6B6B",
      "medium": "#4ECDC4",
      "low": "#95E1D3"
    }
  }
}
```

## 🔍 Quality Assessment

**Verification Checklist**:
- [ ] All tasks scheduled (no failures)
- [ ] No machine conflicts (overlaps)
- [ ] Precedence constraints satisfied
- [ ] Due dates respected (low lateness)
- [ ] Utilization > 30% (not idle)
- [ ] No severe bottlenecks
- [ ] Reasonable makespan

## 📚 Examples

### Quick Test
```bash
uv run orchestrator_main.py \
  --workflow full-manufacturing \
  --input samples/simple/001_simple_square.nc
```

### ISO Test Suite
```bash
uv run orchestrator_main.py \
  --workflow full-manufacturing \
  --input samples/ISO10791/ISO10791_001.nc
```

## 🔗 Related

- [../README.md](../README.md) - Sample overview
- [../../README.md](../../README.md) - Project docs
- [../../agents/cell-schedule-visualizer/README.md](../../agents/cell-schedule-visualizer/README.md) - Agent docs

## ✅ Troubleshooting

**Dashboard Not Generated**:
- Check orchestrator logs for errors
- Verify scheduling succeeded
- Ensure Plotly installed: `uv sync`

**No Data Displayed**:
- Verify scheduling results populated
- Check `gantt_data` section exists
- Review quality_metrics

**Charts Don't Show**:
- Try different browser
- Check browser console
- Verify HTML not corrupted
