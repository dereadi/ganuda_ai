#!/bin/bash
# Test script for SAG Sidebar API endpoints

echo "========================================"
echo "SAG Command Center Sidebar API Tests"
echo "========================================"
echo ""

echo "1. Testing /api/sidebar/alerts"
echo "-------------------------------"
curl -s http://localhost:4000/api/sidebar/alerts | python3 -m json.tool | head -20
echo ""

echo "2. Testing /api/sidebar/triad-status"
echo "------------------------------------"
curl -s http://localhost:4000/api/sidebar/triad-status | python3 -m json.tool
echo ""

echo "3. Testing /api/sidebar/activity"
echo "--------------------------------"
curl -s http://localhost:4000/api/sidebar/activity | python3 -m json.tool | head -30
echo ""

echo "========================================"
echo "All tests completed successfully!"
echo "========================================"
