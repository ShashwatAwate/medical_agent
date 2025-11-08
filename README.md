# Medial Agent - Hospital Resource Allocation System

A Streamlit-based AI agent for intelligent hospital resource allocation using LangGraph and Google Generative AI. The system forecasts resource shortages/surpluses and generates AI-driven recommendations optimized across cost, coverage, fairness, and urgency.

## Project Overview

**Medial Agent** simulates a multi-hospital network where resources (oxygen, ventilators, medication, PPE kits, and custom resources) are dynamically tracked and redistributed. Using AI-powered forecasting and user feedback loops, the system learns to make better allocation decisions over time, balancing multiple objectives to optimize healthcare resource distribution.

### Key Features

- **Synthetic Data Generation**: Generates 14 days of realistic hospital data with events (disasters, weather, seasonal patterns)
- **Intelligent Forecasting**: Rolling-average trend analysis with severity-based multipliers predicts resource shortages
- **AI-Powered Recommendations**: Google Gemini generates human-readable resource transfer suggestions
- **Interactive Feedback Loop**: Accept/reject recommendations to refine future allocations
- **Multi-objective Optimization**: Balances cost efficiency, coverage equity, fairness, and urgency
- **Real-time Tracking**: Monitor specific hospitals and visualize resource trends
- **LangGraph Workflows**: State-based workflow management across 7 sequential decision nodes

---

## System Architecture

### LangGraph Workflow Overview

The application implements a state machine with 7 nodes that orchestrate hospital data analysis and recommendation generation:


START 
  
1. ingest_knowledge 
  
2. ingest_daily_reports 
  
3. forecast_data 
  
4. draw_conclusions 
  
5. build_recommendations 
  
6. save_state 
  
END


### Detailed Node Descriptions

**1. ingest_knowledge** (`agent/data_ingestor.py`)
- Initializes simulation by generating 14 days of synthetic hospital data
- Creates inter-hospital distance matrix for logistics calculations
- Generates baseline resource stocks, usage patterns, and hospital metadata
- **Output**: `window_data` (14-day history), `distances` (hospital distance matrix)

**2. ingest_daily_reports** (`agent/data_ingestor.py`)
- Generates contextual reports explaining resource usage spikes
- Assigns severity levels (mild, moderate, severe, critical) based on event type
- Filters data to only tracked hospitals
- **Output**: `report_data` (event context & severity), `tracking_data` (monitored hospitals only)

**3. forecast_data** (`agent/forecasting.py`)
- Calculates 7-day rolling average trend for each resource per hospital
- Applies severity multipliers (critical = 1.6x, severe = 1.4x, moderate = 1.2x, mild = 1.05x)
- Predicts next-day resource usage combining baseline + trend + severity adjustment
- **Output**: `today_forecasts` (predicted usage for each resource at each hospital)

**4. draw_conclusions** (`agent/forecasting.py`)
- Compares predicted usage against current stock levels
- Identifies shortages (stock < forecast) and surpluses (stock > forecast + 100 units)
- Generates human-readable conclusions about resource imbalances
- **Output**: `shortages`, `surpluses`, `forecast_conclusions` (lists of imbalances)

**5. build_recommendations** (`agent/recommendations.py`)
- Ranks transfer candidates using multi-factor scoring:
  - **Distance Score**: Minimizes transportation cost (closer hospitals preferred)
  - **Coverage Score**: Ensures shortage is substantially met
  - **Fairness Score**: Minimizes equity gaps between hospitals
  - **Urgency Score**: Weights by current event severity
- Calls Google Gemini API to generate natural language recommendations
- Ensures recommendations don't repeat previous ones
- **Output**: `recommendation` (text), `recommendation_justification`, `recommendation_meta` (transfer details)

**6. save_state** (`agent/persistence.py`)
- Persists entire application state to `./sim_outputs/state.json`
- Enables resuming simulations across app restarts
- **Output**: Saved state file for recovery

### Data Flow State Object

The `State` (TypedDict in `agent/core.py`) maintains all workflow data:

```
{
  "sim_date": datetime,              # Current simulation date
  "days_since_update": int,          # Days elapsed since last feedback
  "window_data": DataFrame,          # 14-day historical data all hospitals
  "today_data": DataFrame,           # Current day data all hospitals
  "tracking_data": DataFrame,        # Data for only tracked hospitals
  "distances": DataFrame,            # Inter-hospital distance matrix
  "shortages": list,                 # Identified shortage cases
  "surpluses": list,                 # Identified surplus cases
  "num_hospitals": int,              # Total hospitals in simulation
  "resource_names": list,            # Resources being tracked
  "report_data": dict,               # Current event context & severity
  "today_forecasts": dict,           # Predicted usage per hospital
  "forecast_conclusions": list,      # Human-readable imbalance summary
  "recommendation": str,             # AI-generated transfer suggestion
  "recommendation_justification": str,  # Reasoning for recommendation
  "recommendation_meta": dict,       # Transfer details (from, to, resource, qty)
  "recommendation_weights": dict,    # Cost/Coverage/Fairness/Urgency weights
  "user_feedback": str,              # User's feedback on recommendation
  "done": bool                       # Workflow completion flag
}
```

---

## Data Generation

### Synthetic Data Structure

The `SyntheticData` class (`agent/data/generate_data.py`) generates realistic hospital data:

**Per Hospital (per day):**
- Hospital ID: hos_1, hos_2, ..., hos_N
- Region: north, south, east, west, or central
- Patient count: 500-1000
- Staff count: 50-200
- For each resource:
  - Current stock: 200-800 units
  - Daily usage: 0 to (stock-100) units

**14-Day History:**
- Starts 13 days before current simulation date
- Captures realistic variance in consumption patterns

### Report Generation Process

The `generate_reports()` function creates contextual narratives:

**Event Categories (probabilistic distribution):**
- **Disaster Events (20%)**: flood, earthquake, explosion, epidemic
  - Severity: mild, moderate, severe, critical
  - Example: "A critical flood in north region has overwhelmed hospitals with new patients"

- **Weather Events (30%)**: heat wave, blizzard, heavy rain, storm
  - Severity: mild, moderate, severe, critical
  - Example: "The ongoing heat wave has caused severe strain on oxygen across central"

- **Seasonal Events (30%)**: flu outbreak, pollen allergies, tourist season, festivals
  - Lower severity (typically mild-moderate)
  - Example: "During flu outbreak, hospitals saw steady rise in PPE kit demand"

- **Normal Operations (20%)**: no significant spikes
  - Example: "Hospital reports stable operations; no shortages detected"

**Usage Delta Calculation:**
- If event suggests "increased" or "higher" usage: add 10-40% to base usage
- Multiplier applies to resource consumption for that day
- Creates realistic patterns for forecasting to detect

### Distance Matrix

- Random distances between hospital pairs: 5-500 km
- Diagonal = 0 (distance from hospital to itself)
- Used by recommendation engine to optimize logistics costs
- Example (5 hospitals):
```
     hos_1  hos_2  hos_3  hos_4  hos_5
hos_1   0     150    320     45    280
hos_2  150     0     210    175    350
hos_3  320    210     0     290    120
hos_4   45    175    290     0     360
hos_5  280    350    120    360     0
```

### Example Generated Data

```
hospital,region,date,patients,staff,oxygen_stock,oxygen_usage,ventilators_stock,ventilators_usage,medication_TB_stock,medication_TB_usage,ppe_kits_stock,ppe_kits_usage
hos_1,north,2025-01-01,650,120,550,320,600,150,480,210,720,145
hos_1,north,2025-01-02,680,125,480,350,550,160,450,220,680,155
hos_2,south,2025-01-01,780,95,480,410,520,200,520,280,650,190
```

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** (3.8+ minimum, but 3.10+ recommended)
- **pip** (Python package manager)
- **git** (for version control)
- **Google API Key** (free from https://aistudio.google.com/apikey)

---

## Usage Workflow (check INSTALLATION.md first to build and run the project.)

### Step 1: Initialize Simulation (Home Tab)

1. Select "Home" from the sidebar
2. Choose simulation mode:
   - **Start New Simulation**: Create a fresh 14-day dataset
   - **Continue Previous Simulation**: Resume from saved state
3. Configure:
   - Number of hospitals (2-20)
   - Resources to track (oxygen, ventilators, medication_TB, ppe_kits)
   - Custom resources (optional, comma-separated)
4. Click "Start Simulation"

### Step 2: Set Up Tracking (Tracking Tab)

1. Select "Tracking" from the sidebar
2. Choose which hospitals to monitor for recommendations
3. Only tracked hospitals appear in transfer recommendations
4. Click "Update Tracking"

### Step 3: Get Recommendations (Recommend Tab)

1. Select "Recommend" from the sidebar
2. Click "Get Recommendation" to run the full workflow
3. System will:
   - Forecast resource needs for next 24 hours
   - Identify shortages and surpluses
   - Generate AI recommendation for transfer
4. Review recommendation and justification

### Step 4: Approve or Reject Recommendation

**If Accept:**
- Optionally adjust transfer quantities per hospital pair
- Click "Confirm" for each transfer pair
- Click "Submit Feedback"
- Resource stocks update immediately
- Simulation advances 1 day

**If Reject:**
- Provide reasoning for rejection (e.g., "too far away", "priority should be fairness")
- Click "Submit Rejection"
- System analyzes feedback using NLP to adjust weights
- Simulation advances 1 day

### Step 5: Monitor Trends (Insights Tab)

1. Select "Insights" from the sidebar
2. Select hospital and resource from dropdowns
3. View 14-day trend chart
4. See summary statistics (average, min, max)
5. Compare all resources over time

---

## Recommendation Weights

The system balances 4 key metrics to generate recommendations. Weights range from 0.0-1.0 (default all 0.5):

- **Cost (0.0-1.0)**: Preference for closer hospitals, minimizing transportation costs
- **Coverage (0.0-1.0)**: Ensuring shortage is substantially resolved
- **Fairness (0.0-1.0)**: Minimizing equity gaps between hospitals
- **Urgency (0.0-1.0)**: Prioritizing by event severity

**Weight Adjustments:**
- **Accept recommendation**: All weights increase by 0.02 (system learns this was a good decision)
- **Reject recommendation**: Weights decrease based on semantic similarity to your feedback reason
  - Feedback mentioning "cost/distance" → decreases cost weight
  - Feedback mentioning "fairness/equality" → decreases fairness weight
  - And so on...

---

## Project Structure

```
medial-agent/
├── main.py                         # Streamlit app entry point & UI flows
├── agent/
│   ├── core.py                     # State TypedDict, LLM client setup, model definition
│   ├── data_ingestor.py            # ingest_knowledge & ingest_daily_reports nodes
│   ├── data_insights.py            # show_insights visualization
│   ├── forecasting.py              # forecast_data & draw_conclusions nodes
│   ├── recommendations.py          # build_recommendations & get_feedback nodes
│   ├── persistence.py              # save_state node & load/save functions
│   ├── tracking.py                 # Hospital tracking setup
│   ├── utils.py                    # Helper functions, embeddings, LLM parsing
│   └── data/
│       └── generate_data.py        # SyntheticData class for data generation
├── sim_data/
│   └── simulation.csv              # Generated synthetic data (auto-created)
├── sim_outputs/
│   └── state.json                  # Persisted application state (auto-created)
├── .env                            # Environment variables (create manually)
├── pyproject.toml                  # Project configuration and dependencies
└── README.md                       # This file
```

## Features

- **AI-Powered Analysis**: Uses Google Generative AI for intelligent media analysis
- **LangGraph Workflows**: State-based workflow management
- **Semantic Search**: Utilizes embeddings and FAISS for similarity search
- **Forecasting**: Predict trends and patterns in media data
- **Personalized Recommendations**: ML-based recommendation engine
- **Data Persistence**: Store and retrieve analysis results
- **Activity Tracking**: Monitor and track user interactions

## Troubleshooting

### Issue: ModuleNotFoundError

**Solution:** Ensure all dependencies are installed:
\`\`\`bash
pip install -e .
\`\`\`

Or install individually:
\`\`\`bash
pip install streamlit numpy pandas langgraph google-generativeai python-dotenv sentence-transformers faiss-cpu scikit-learn
\`\`\`

### Issue: GEMINI_API_KEY not found

**Solution:** Verify that your \`.env\` file exists in the project root and contains:
\`\`\`env
GEMINI_API_KEY=your_key_here
\`\`\`

Make sure the file is named \`.env\` (not \`.env.txt\` or other variations). Restart Streamlit after adding the key.

### Issue: "Cannot Update Tracking! Run a recommendation first"

**Solution:** The system needs forecast data before tracking specific hospitals.
1. Go to "Recommend" tab
2. Click "Get Recommendation" to generate initial forecasts
3. Return to "Tracking" tab and try again

### Issue: "Could not load saved state"

**Solution:** The state file is corrupted or incomplete.
1. Delete \`./sim_outputs/state.json\`
2. Start a new simulation from the Home tab
3. This will create a fresh state file

### Issue: Port 8501 already in use

**Solution:** Run Streamlit on a different port:
\`\`\`bash
streamlit run main.py --server.port 8502
\`\`\`

### Issue: Slow performance on first run

**Solution:** Sentence-transformers will download embedding models (~400MB) on first use. This is normal and only happens once.

### Issue: Forecast seems unrealistic

**Solution:** Check the report data severity level:
- Mild events: 1.05x multiplier
- Moderate events: 1.2x multiplier
- Severe events: 1.4x multiplier
- Critical events: 1.6x multiplier

This is intentional to account for emergency scenarios where resource needs spike dramatically.

### Issue: Recommendation keeps repeating

**Solution:** The system automatically avoids repeating recommendations. If stuck:
1. Reject the recommendation with feedback explaining why
2. System will adjust weights to prioritize different factors
3. Click "Get Recommendation" again for a new suggestion

---
### Adding New Resources

1. Open \`main.py\`
2. Modify \`base_resources\` list in the Home section
3. Resources automatically generate stock/usage data columns in generated data

### Modifying Recommendation Scoring

Edit the scoring function in \`agent/recommendations.py\`:
\`\`\`python
distance_score = w_cost * (1 - (avg_dist / max_dist))
coverage_score = w_coverage * (min(shortage, available_surplus) / shortage)
fairness_score = w_fairness * (1 - abs(available_surplus - shortage) / (available_surplus + shortage))
urgency_score = w_urgency * severity_score[severity]
score = distance_score + coverage_score + fairness_score + urgency_score
\`\`\`

### Customizing Event Types

Edit \`agent/data/generate_data.py\` to add custom event types, modify severity multipliers, or adjust event probabilities.

---

## Dependencies

See \`pyproject.toml\` for the complete list:
- **streamlit**: Web UI framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **langgraph**: Workflow orchestration and state management
- **google-generativeai**: Gemini API access for recommendations
- **sentence-transformers**: NLP embeddings for feedback analysis
- **faiss-cpu**: Vector similarity search and clustering
- **scikit-learn**: Machine learning utilities (cosine similarity)
- **python-dotenv**: Environment variable management

---
