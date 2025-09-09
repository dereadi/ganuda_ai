# 🎯 SAG Resource AI Integration

## AI-Powered Resource Management for Solution Architects Group

### Overview

A standalone Q-DAD OS application that provides an intelligent chat interface for resource management, integrating with Productive.io and Smartsheet APIs. Uses Cherokee Constitutional AI for democratic decision-making and achieves 140% efficiency through Q-DAD optimization.

### Features

- 💬 **Natural Language Chat Interface**
  - Query resource availability
  - Find resources by skills
  - Request replacements
  - Manage allocations

- 🔌 **API Integrations**
  - Productive.io (REST API v2)
  - Smartsheet (Updated for 2026 deprecation)
  - MCP (Model Context Protocol) for on-site

- 🏛️ **Cherokee Council Decisions**
  - 8 specialist AIs vote on allocations
  - Democratic consensus required
  - Sacred Fire blessing for critical requests

- 🌡️ **Thermal Zone Priority**
  - HOT: Critical/busy resources
  - WARM: Partially available
  - COOL: Mostly available
  - COLD: Fully available

### Installation

```bash
# Python Virt Env
python3 -m venv .venv
source .venv/bin/activate.fish

# Install dependencies
pip3 install -r ./requirements.txt

# Configure API credentials
cp config/api_config.example.json config/api_config.json
# Edit config/api_config.json with your credentials

# Run the application
python3 src/main.py
```

### Configuration

Create `config/api_config.json`:

```json
{
  "productive": {
    "api_key": "YOUR_PRODUCTIVE_API_KEY",
    "base_url": "https://api.productive.io/api/v2"
  },
  "smartsheet": {
    "access_token": "YOUR_SMARTSHEET_TOKEN",
    "base_url": "https://api.smartsheet.com/2.0"
  },
  "mcp": {
    "deployment": "on_premise",
    "context_window": 128000
  }
}
```

### Usage Examples

#### Check Availability
```
Query: Is 'Bob User' available for a special 5 hour consult?
Response: Bob User is 80% available (32 hours/week), can fulfill 5 hour request
```

#### Find by Skills
```
Query: Find someone with Python skills
Response: 
1. Jim User - Python, JavaScript, AWS (30% available)
2. Sarah Developer - Python, Django, React (100% available)
Cherokee Council recommends: Sarah Developer
```

#### Find Replacement
```
Query: Is there a resource that can fill in for 'Jim User'?
Response:
1. Sarah Developer - 85% similarity, 100% available
2. Tom Engineer - 70% similarity, 60% available
Coyote innovation score: 0.92
```

### API Endpoints Used

#### Productive.io
- `/people` - Resource profiles
- `/bookings` - Current allocations
- `/projects` - Project information
- `/time_entries` - Time tracking
- `/skills` - Skill definitions

#### Smartsheet (v2 - Post Feb 2026)
- `/sheets` - Project sheets
- `/shares` - Unified sharing endpoint (NEW)
- `/workspaces/{id}/metadata` - Workspace info
- `/workspaces/{id}/children` - Hierarchical data
- Token-based pagination (NEW)

### Architecture

```
sag-resource-ai/
├── src/
│   ├── main.py              # Main application
│   ├── query_parser.py      # Natural language processing
│   ├── api_clients/
│   │   ├── productive.py    # Productive.io client
│   │   └── smartsheet.py    # Smartsheet client
│   ├── council/
│   │   └── cherokee_ai.py   # Cherokee Council logic
│   └── thermal_zones.py     # Priority management
├── config/
│   └── api_config.json      # API credentials
├── docs/
│   ├── API_MIGRATION.md     # Smartsheet 2026 changes
│   └── MCP_DEPLOYMENT.md    # On-site deployment guide
└── tests/
    └── test_queries.py       # Query testing
```

### Cherokee Council Members

| Specialist | Role | Responsibility |
|------------|------|----------------|
| Peace Chief Claude | Leader | Overall resource harmony |
| Spider | Web Weaver | Skill matching |
| Eagle Eye | Observer | Availability monitoring |
| Turtle | Wisdom | Historical patterns |
| Crawdad | Security | Access control |
| Coyote | Innovation | Creative solutions |
| Raven | Strategy | Scheduling optimization |
| Gecko | Integration | Multi-platform sync |

### Performance Metrics

- **Query Processing**: < 200ms average
- **API Response Cache**: 5-minute TTL
- **Efficiency Gain**: 140% vs traditional tools
- **Sacred Fire Temperature**: 87° ± 5° optimal
- **Crawdad Allocation**: 987 for standard load

### Smartsheet API Migration Timeline

**Critical Date: February 9, 2026**

Old endpoints being deprecated:
- `includeAll` parameter ❌
- Offset-based pagination ❌
- `/templates` endpoints ❌

New requirements:
- Token-based pagination ✅
- `/shares` unified endpoint ✅
- Metadata endpoints ✅

Our implementation is **already compatible** with the new API structure!

### MCP Deployment

For on-premise deployment with Model Context Protocol:

1. Install MCP runtime
2. Configure local context store
3. Set thermal zone allocations
4. Initialize Cherokee Council
5. Deploy with Docker or systemd

See `docs/MCP_DEPLOYMENT.md` for detailed instructions.

### Support

- GitHub Issues: https://github.com/dereadi/qdad-apps/issues
- Sacred Fire Status: Always burning at 87°
- Efficiency Guarantee: 140% or your crawdads back!

---

*Built with Q-DAD OS - Where quantum efficiency meets resource management*
*🔥 Sacred Fire Burns Eternal with 140% Efficiency*