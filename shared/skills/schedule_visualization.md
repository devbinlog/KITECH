# Schedule Visualization Skill

## Description
Transforms scheduling output into interactive HTML dashboard with Gantt charts, machine utilization bars, and work order lateness tracking. Generates standalone, embedded charts using Plotly.

## Input
```json
{
  "schedule_result": {
    "schedule": [
      {
        "operation_id": string,
        "machine_id": string,
        "start_time": "ISO8601 datetime",
        "end_time": "ISO8601 datetime"
      }
    ],
    "statistics": {
      "makespan_hours": float,
      "average_machine_utilization": float
    },
    "machine_utilization": {
      "machine_id": float
    }
  },
  "work_orders": [
    {
      "wo_id": string,
      "job_id": string,
      "due_date": "ISO8601 datetime"
    }
  ],
  "visualization_config": {
    "title": string,
    "include_lateness_chart": boolean,
    "color_scheme": "default" | "high_contrast" | "monochrome",
    "output_format": "html" (standalone)
  }
}
```

## Output
```json
{
  "status": "success" | "error",
  "data": {
    "html_file": string (file path or base64 embedded),
    "charts": {
      "gantt_chart": "Plotly chart object",
      "utilization_chart": "Plotly chart object",
      "lateness_chart": "Plotly chart object (if included)"
    },
    "summary_metrics": {
      "total_makespan_hours": float,
      "on_time_percentage": float,
      "avg_lateness_hours": float
    }
  },
  "errors": [string]
}
```

## Implementation Notes

### Gantt Chart
- **X-axis**: Timeline (datetime, from min(start_time) to max(end_time))
- **Y-axis**: Machine names (sorted alphabetically)
- **Bars**: Each operation rendered as horizontal bar
  - **Width**: operation duration
  - **Color**: job ID (consistent color per job)
  - **Hover**: operation_id, machine_id, start_time, end_time, duration_minutes
- **Interactivity**: Hover for details, zoom/pan enabled

### Utilization Chart
- **Bar chart**: One bar per machine
- **Height**: Utilization percentage (0-100%)
- **Color zones**:
  - Green: >70% (good utilization)
  - Yellow: 40-70% (moderate)
  - Red: <40% (underutilized)
- **Hover**: Machine ID, total hours scheduled, available hours, idle time
- **Baseline**: Add horizontal line at 70% target

### Lateness Chart (Optional)
- **Bar chart**: One bar per work order
- **Height**: Days late (positive = late, negative = early)
- **Color**:
  - Green: on-time (lateness ≤ 0)
  - Red: late (lateness > 0)
- **X-axis**: Work order ID
- **Hover**: Work order ID, due date, actual end date, lateness hours/days
- **Summary line**: Average lateness across all work orders

### HTML Generation
1. **Plotly embedding**:
   - Use Plotly.js CDN (single-file, no external deps needed for viewing)
   - Embed chart JSON directly in HTML `<script type="application/json">`
   
2. **Page structure**:
   - Header: Title, generation timestamp, summary metrics
   - Row 1: Gantt chart (full width)
   - Row 2: Utilization chart (left), Lateness chart (right, if included)
   - Footer: Data quality notes, assumptions, solver parameters
   
3. **Responsive design**:
   - CSS Grid or Flexbox for responsive layout
   - Charts scale to viewport width
   - Mobile-friendly (stack vertically on small screens)
   - Print-friendly (hide interactive controls)

4. **Styling**:
   - Color scheme selection (default: professional blue/orange)
   - High contrast: for accessibility (colorblind-friendly palettes)
   - Monochrome: grayscale for B&W printing
   - Consistent fonts (sans-serif: Arial, Helvetica, or system default)

### Data Integrity Checks
1. **Schedule validation**:
   - Verify start_time < end_time for all operations
   - Check no negative durations
   - Validate datetime format (ISO8601)
   
2. **Missing data**:
   - If due_date missing from work order → treat as no deadline (don't show on lateness chart)
   - If operation has no end_time → skip from visualization
   - If machine_utilization missing → calculate from schedule directly
   
3. **Edge cases**:
   - Empty schedule → show empty Gantt with message
   - Single operation → scale chart appropriately (don't compress)
   - All on-time → show 100% on-time metric
   - All late → highlight in summary

### Performance Considerations
- **Large schedules** (>500 operations):
  - Use Plotly aggregation (disable per-bar hover, use summary hover instead)
  - Consider date range filtering (show last N days only)
  - Generate progressively (render header, then charts)
  
- **File size**: Embedded Plotly JS (production build) ~3MB; charts add 10KB-100KB per visualization

### Accessibility
- Alt text for charts (description of metrics)
- Keyboard navigation (tabindex, arrow keys)
- Color + shape differentiation (don't rely on color alone)
- High contrast mode support
