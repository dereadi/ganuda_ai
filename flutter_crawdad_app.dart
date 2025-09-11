#!/usr/bin/env dart
// 🦞 CELLULAR CRAWDAD: FLUTTER APP STRUCTURE
// One codebase, two platforms, infinite trails

import 'package:flutter/material.dart';
import 'package:sqflite/sqflite.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:nearby_connections/nearby_connections.dart';
import 'package:geolocator/geolocator.dart';

// ============================================================================
// MAIN APP STRUCTURE - Testing Q-DAD efficiency with each build
// ============================================================================

void main() {
  runApp(CellularCrawdadApp());
}

class CellularCrawdadApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Cellular Crawdad',
      theme: ThemeData(
        primaryColor: Color(0xFF8B4513), // Crawdad brown
        accentColor: Color(0xFF00CED1),  // Water blue
      ),
      home: CrawdadHome(),
    );
  }
}

// ============================================================================
// TRAIL DATA MODEL
// ============================================================================

class PheromoneTrail {
  final String id;
  final double latitude;
  final double longitude;
  final String towerId;
  final int signalStrength;
  final bool success;
  final DateTime timestamp;
  double strength; // Decays over time
  
  PheromoneTrail({
    required this.id,
    required this.latitude,
    required this.longitude,
    required this.towerId,
    required this.signalStrength,
    required this.success,
    required this.timestamp,
    this.strength = 1.0,
  });
  
  // Calculate trail decay
  double getCurrentStrength() {
    final age = DateTime.now().difference(timestamp).inMinutes;
    return strength * exp(-0.01 * age); // Exponential decay
  }
  
  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'latitude': latitude,
      'longitude': longitude,
      'tower_id': towerId,
      'signal_strength': signalStrength,
      'success': success ? 1 : 0,
      'timestamp': timestamp.toIso8601String(),
      'strength': strength,
    };
  }
}

// ============================================================================
// Q-DAD ENGINE (Simplified for MVP)
// ============================================================================

class QuantumCrawdadEngine {
  static final QuantumCrawdadEngine _instance = QuantumCrawdadEngine._internal();
  factory QuantumCrawdadEngine() => _instance;
  QuantumCrawdadEngine._internal();
  
  Database? _database;
  final List<PheromoneTrail> _localTrails = [];
  bool _isHibernating = false;
  
  // Initialize the Q-DAD
  Future<void> initialize() async {
    _database = await openDatabase(
      'crawdad_trails.db',
      version: 1,
      onCreate: (db, version) {
        return db.execute('''
          CREATE TABLE trails(
            id TEXT PRIMARY KEY,
            latitude REAL,
            longitude REAL,
            tower_id TEXT,
            signal_strength INTEGER,
            success INTEGER,
            timestamp TEXT,
            strength REAL
          )
        ''');
      },
    );
  }
  
  // Process backwards from successful connections
  Future<PheromoneTrail?> findBestTrail(Position position) async {
    if (_isHibernating) return null;
    
    // Query nearby trails (retrograde - start from successes)
    final trails = await _database!.query(
      'trails',
      where: 'success = 1 AND strength > 0.3',
      orderBy: 'strength DESC',
    );
    
    // Find closest successful trail
    PheromoneTrail? bestTrail;
    double minDistance = double.infinity;
    
    for (var trailMap in trails) {
      final trail = PheromoneTrail(
        id: trailMap['id'] as String,
        latitude: trailMap['latitude'] as double,
        longitude: trailMap['longitude'] as double,
        towerId: trailMap['tower_id'] as String,
        signalStrength: trailMap['signal_strength'] as int,
        success: trailMap['success'] == 1,
        timestamp: DateTime.parse(trailMap['timestamp'] as String),
        strength: trailMap['strength'] as double,
      );
      
      final distance = Geolocator.distanceBetween(
        position.latitude,
        position.longitude,
        trail.latitude,
        trail.longitude,
      );
      
      if (distance < minDistance && distance < 100) { // Within 100 meters
        minDistance = distance;
        bestTrail = trail;
      }
    }
    
    return bestTrail;
  }
  
  // Hibernate when not needed (battery saving)
  void hibernate() {
    _isHibernating = true;
    print("🦞 Q-DAD hibernating in the mud...");
  }
  
  void wake() {
    _isHibernating = false;
    print("🦞 Q-DAD awakening!");
  }
}

// ============================================================================
// MAIN UI - Shows the magic happening
// ============================================================================

class CrawdadHome extends StatefulWidget {
  @override
  _CrawdadHomeState createState() => _CrawdadHomeState();
}

class _CrawdadHomeState extends State<CrawdadHome> {
  final QuantumCrawdadEngine _qDad = QuantumCrawdadEngine();
  ConnectivityResult _connectivity = ConnectivityResult.none;
  int _signalStrength = 0;
  int _trailsShared = 0;
  int _trailsReceived = 0;
  bool _isCrowdMode = false;
  double _batteryImpact = 0.0;
  
  @override
  void initState() {
    super.initState();
    _initializeCrawdad();
  }
  
  Future<void> _initializeCrawdad() async {
    await _qDad.initialize();
    _startMonitoring();
    _startP2PSharing();
  }
  
  void _startMonitoring() {
    // Monitor connectivity changes
    Connectivity().onConnectivityChanged.listen((result) {
      setState(() {
        _connectivity = result;
      });
      
      // Create trail for this connection attempt
      _createTrail(result != ConnectivityResult.none);
    });
  }
  
  void _startP2PSharing() async {
    // Initialize Nearby Connections for P2P trail sharing
    await Nearby().askLocationPermission();
    
    // Start advertising as a crawdad
    await Nearby().startAdvertising(
      "crawdad_${DateTime.now().millisecondsSinceEpoch}",
      Strategy.P2P_CLUSTER,
      onConnectionInitiated: (endpointId, info) {
        // Accept all crawdad connections
        Nearby().acceptConnection(
          endpointId,
          onPayLoadRecieved: (endpointId, payload) {
            // Received a trail from another crawdad!
            setState(() {
              _trailsReceived++;
            });
          },
        );
      },
      onConnectionResult: (endpointId, status) {
        if (status == Status.CONNECTED) {
          // Share our best trails
          _shareTrails(endpointId);
        }
      },
      onDisconnected: (endpointId) {
        print("Crawdad disconnected: $endpointId");
      },
    );
  }
  
  void _createTrail(bool success) async {
    final position = await Geolocator.getCurrentPosition();
    
    final trail = PheromoneTrail(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      latitude: position.latitude,
      longitude: position.longitude,
      towerId: "tower_${_connectivity.name}", // Simplified
      signalStrength: _signalStrength,
      success: success,
      timestamp: DateTime.now(),
    );
    
    // Save to database
    await _qDad._database?.insert('trails', trail.toMap());
  }
  
  void _shareTrails(String endpointId) async {
    // Share our strongest trails
    final trails = await _qDad._database?.query(
      'trails',
      where: 'success = 1',
      orderBy: 'strength DESC',
      limit: 10,
    );
    
    if (trails != null) {
      for (var trail in trails) {
        Nearby().sendBytesPayload(
          endpointId,
          trail.toString().codeUnits,
        );
        setState(() {
          _trailsShared++;
        });
      }
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('🦞 Cellular Crawdad'),
        actions: [
          IconButton(
            icon: Icon(_isCrowdMode ? Icons.group : Icons.person),
            onPressed: () {
              setState(() {
                _isCrowdMode = !_isCrowdMode;
                if (_isCrowdMode) {
                  _qDad.wake();
                } else {
                  _qDad.hibernate();
                }
              });
            },
          ),
        ],
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFF87CEEB), // Sky blue
              Color(0xFF8B7355), // Mud brown
            ],
          ),
        ),
        child: Column(
          children: [
            // Signal Strength Indicator
            Expanded(
              child: Center(
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    // Ripple effect for active scanning
                    if (_isCrowdMode)
                      AnimatedContainer(
                        duration: Duration(seconds: 2),
                        width: 200,
                        height: 200,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.blue.withOpacity(0.3),
                        ),
                      ),
                    // Crawdad icon
                    Icon(
                      Icons.wifi,
                      size: 100,
                      color: _getSignalColor(),
                    ),
                    // Signal strength text
                    Positioned(
                      bottom: 0,
                      child: Text(
                        '${_signalStrength}%',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // Stats Dashboard
            Container(
              padding: EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.black87,
                borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
              ),
              child: Column(
                children: [
                  Text(
                    _isCrowdMode ? '🦞 SWARM MODE ACTIVE' : '💤 HIBERNATING',
                    style: TextStyle(
                      color: _isCrowdMode ? Colors.greenAccent : Colors.grey,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 20),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildStat('Trails\nShared', _trailsShared.toString()),
                      _buildStat('Trails\nReceived', _trailsReceived.toString()),
                      _buildStat('Battery\nImpact', '${_batteryImpact.toStringAsFixed(1)}%'),
                    ],
                  ),
                  SizedBox(height: 20),
                  // Connection status
                  Container(
                    padding: EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.check_circle, color: Colors.green),
                        SizedBox(width: 10),
                        Text(
                          'Following Optimal Trail',
                          style: TextStyle(color: Colors.green),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildStat(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            color: Colors.white,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            color: Colors.grey,
            fontSize: 12,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
  
  Color _getSignalColor() {
    if (_signalStrength > 75) return Colors.green;
    if (_signalStrength > 50) return Colors.yellow;
    if (_signalStrength > 25) return Colors.orange;
    return Colors.red;
  }
}

// ============================================================================
// PUBSPEC.YAML DEPENDENCIES (Save as pubspec.yaml)
// ============================================================================
/*
name: cellular_crawdad
description: Quantum Crawdad Cellular Optimization

dependencies:
  flutter:
    sdk: flutter
  sqflite: ^2.3.0
  connectivity_plus: ^5.0.0
  nearby_connections: ^3.3.0
  geolocator: ^10.1.0
  permission_handler: ^11.0.0
  battery_plus: ^5.0.0
  
dev_dependencies:
  flutter_test:
    sdk: flutter

flutter:
  uses-material-design: true
  assets:
    - assets/crawdad_logo.png
*/

// ============================================================================
// BUILD COMMANDS
// ============================================================================
/*
# Setup Flutter
flutter create cellular_crawdad
cd cellular_crawdad

# Add this code to lib/main.dart

# Install dependencies
flutter pub get

# Run on Android
flutter run

# Build Android APK
flutter build apk --release

# Run on iOS (needs Mac)
flutter run --release

# Build iOS
flutter build ios --release

# Deploy to TestFlight
cd ios
fastlane beta
*/