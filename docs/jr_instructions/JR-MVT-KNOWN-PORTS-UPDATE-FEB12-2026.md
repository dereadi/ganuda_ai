# Jr Instruction: Update MVT Scanner Known Ports for All Nodes

**Priority**: P1 — Reduce false positives
**Kanban**: #549
**Assigned Jr**: Software Engineer Jr.

## Step 1: Update KNOWN_PORTS with all federation services

File: `/ganuda/scripts/security/mvt_fleet_scanner.py`

<<<<<<< SEARCH
KNOWN_PORTS = {
    "redfin": {22, 80, 443, 3001, 4000, 5555, 8000, 8080, 9090},
    "bluefin": {22, 3000, 5432, 8090, 8091, 8092, 9090},
    "greenfin": {22, 3128, 8003, 9080, 9090},
}
=======
KNOWN_PORTS = {
    "redfin": {22, 53, 80, 443, 631, 2019, 3000, 4000, 5432, 5555, 5556,
               8000, 8001, 8002, 8003, 8080, 8081, 8090},
    "bluefin": {22, 3000, 5432, 8090, 8091, 8092},
    "greenfin": {22, 5080, 5081, 8003, 9080},
}
>>>>>>> REPLACE

## For Seven Generations
