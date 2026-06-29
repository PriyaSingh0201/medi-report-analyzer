# Problem Summary Features Documentation

## Overview
New comprehensive problem summary features have been added to the report analyzer to provide detailed analytics and insights about health problems detected across all user reports.

## New Features Added

### 1. **Problem Summary Aggregation** (`/api/summary/problems`)
- **Endpoint**: `GET /api/summary/problems`
- **Description**: Gets aggregated list of all unique problems detected across user reports
- **Returns**:
  - Total number of unique problems
  - Each problem with:
    - Name/Description
    - Frequency (how many times detected)
    - Associated severity levels
    - Most common severity
  - Sorted by frequency (most common first)

**Example Response**:
```json
{
  "message": "Problem summary retrieved successfully!",
  "summary": {
    "total_problems": 15,
    "problems": [
      {
        "name": "Low Hemoglobin",
        "count": 8,
        "severity_levels": ["Critical", "Moderate"],
        "most_common_severity": "Critical"
      },
      {
        "name": "High Glucose (High)",
        "count": 5,
        "severity_levels": ["Moderate"],
        "most_common_severity": "Moderate"
      }
    ]
  }
}
```

---

### 2. **Problems Grouped by Severity** (`/api/summary/problems-by-severity`)
- **Endpoint**: `GET /api/summary/problems-by-severity`
- **Description**: Lists all problems organized by their severity classification
- **Returns**: 
  - Problems categorized under: Normal, Moderate, Critical
  - Each severity level contains list of problems found at that level

**Example Response**:
```json
{
  "message": "Problems by severity retrieved successfully!",
  "data": {
    "Normal": [],
    "Moderate": [
      "Vitamin D (Low)",
      "Platelets (Low)"
    ],
    "Critical": [
      "Hemoglobin (Low)",
      "TSH (High)"
    ]
  }
}
```

---

### 3. **Problem Frequency Analysis** (`/api/summary/problems-frequency`)
- **Endpoint**: `GET /api/summary/problems-frequency`
- **Description**: Analyzes problem trends and frequency patterns across reports
- **Returns**:
  - Top 10 most frequent problems with detailed metrics:
    - Frequency count
    - Number of reports containing the problem
    - First seen date
    - Last seen date (trend tracking)
  - Recent problems from latest report
  - Total unique problems

**Example Response**:
```json
{
  "message": "Problem frequency analysis retrieved successfully!",
  "data": {
    "most_frequent": [
      {
        "name": "Low Hemoglobin",
        "frequency": 12,
        "appears_in_reports": 8,
        "first_seen": "2024-01-15T10:30:00",
        "last_seen": "2024-06-20T14:45:00"
      }
    ],
    "recent_problems": [
      "High Glucose",
      "Low Vitamin D"
    ],
    "total_unique_problems": 15
  }
}
```

---

### 4. **Problem Statistics** (`/api/summary/problems-stats`)
- **Endpoint**: `GET /api/summary/problems-stats`
- **Description**: Comprehensive statistical overview of problems detected
- **Returns**:
  - Total reports analyzed
  - Total problems detected across all reports
  - Problem count breakdown by severity
  - Average problems per report
  - Maximum problems in single report
  - Number of reports containing problems

**Example Response**:
```json
{
  "message": "Problem statistics retrieved successfully!",
  "statistics": {
    "total_reports": 20,
    "total_problems_detected": 45,
    "problems_by_severity": {
      "Normal": 2,
      "Moderate": 12,
      "Critical": 8
    },
    "average_problems_per_report": 2.25,
    "max_problems_in_report": 6,
    "reports_with_problems": 20
  }
}
```

---

## How to Use These Features

### Via Frontend (JavaScript/AJAX)
```javascript
// Get problem summary
fetch('/api/summary/problems')
  .then(res => res.json())
  .then(data => console.log(data.summary));

// Get problems by severity
fetch('/api/summary/problems-by-severity')
  .then(res => res.json())
  .then(data => console.log(data.data));

// Get frequency analysis
fetch('/api/summary/problems-frequency')
  .then(res => res.json())
  .then(data => console.log(data.data));

// Get statistics
fetch('/api/summary/problems-stats')
  .then(res => res.json())
  .then(data => console.log(data.statistics));
```

### Via cURL/Command Line
```bash
# Get problem summary
curl -X GET http://localhost:5000/api/summary/problems \
  -H "Authorization: Bearer <token>"

# Get problems by severity
curl -X GET http://localhost:5000/api/summary/problems-by-severity \
  -H "Authorization: Bearer <token>"

# Get frequency analysis
curl -X GET http://localhost:5000/api/summary/problems-frequency \
  -H "Authorization: Bearer <token>"

# Get statistics
curl -X GET http://localhost:5000/api/summary/problems-stats \
  -H "Authorization: Bearer <token>"
```

---

## Implemented Functions in models.py

### 1. `get_problem_summary(user_id)`
Aggregates all problems from user's reports with frequency analysis.

### 2. `get_problem_summary_by_severity(user_id)`
Groups problems by severity level for categorized view.

### 3. `get_problem_frequency_analysis(user_id)`
Analyzes problem frequency trends with historical tracking.

### 4. `get_problem_statistics(user_id)`
Provides comprehensive problem statistics and metrics.

---

## Benefits

1. **Quick Health Overview**: Users can quickly see what health issues they've had
2. **Trend Tracking**: See which problems are recurring and most common
3. **Severity Awareness**: Understand which problems are critical vs moderate
4. **Data-Driven Insights**: Make informed decisions about health management
5. **Historical Context**: Track problem patterns over time
6. **Actionable Metrics**: Understand problem frequency and impact

---

## Integration with Dashboard

These endpoints can be integrated into the dashboard to display:
- Problem widget showing top problems
- Severity pie chart
- Trending problems timeline
- Problem frequency bar chart
- Statistics dashboard

---

## API Response Codes

- `200 OK`: Successfully retrieved data
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Report not found
- `500 Internal Server Error`: Server processing error

---

## Notes

- All endpoints require valid JWT authentication token
- Data is analyzed only for the authenticated user's reports
- Problems are extracted from both alerts and key_findings in reports
- Duplicates and similar problems are cleaned up for accurate analysis
- Frequency analysis considers last 50 reports for performance optimization
