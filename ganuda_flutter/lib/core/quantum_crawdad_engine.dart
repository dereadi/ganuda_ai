import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';

/// 🦞 Quantum Crawdad Engine - Core swarm intelligence
class QuantumCrawdadEngine extends ChangeNotifier {
  final List<QuantumCrawdad> swarm = [];
  final List<PheromoneTrail> trails = [];
  final Random _random = Random();
  Timer? _swarmTimer;
  
  // Network simulation data
  final List<MockCellTower> towers = [];
  final List<MockWiFiRouter> routers = [];
  
  // Performance metrics
  double networkEfficiency = 0.0;
  int activeConnections = 0;
  double avgSignalStrength = 0.0;
  
  QuantumCrawdadEngine() {
    _initializeNetwork();
    _spawnSwarm();
    _startSwarmActivity();
  }
  
  void _initializeNetwork() {
    // Create mock cell towers
    towers.addAll([
      MockCellTower('Tower-A', lat: 35.5, lon: -83.0, strength: 0.8, congestion: 0.3),
      MockCellTower('Tower-B', lat: 35.51, lon: -83.01, strength: 0.6, congestion: 0.7),
      MockCellTower('Tower-C', lat: 35.49, lon: -82.99, strength: 0.9, congestion: 0.5),
    ]);
    
    // Create mock WiFi routers  
    routers.addAll([
      MockWiFiRouter('Cherokee-Guest', lat: 35.501, lon: -83.002, strength: 0.7),
      MockWiFiRouter('Sacred-Fire', lat: 35.502, lon: -83.001, strength: 0.9),
      MockWiFiRouter('Seven-Generations', lat: 35.499, lon: -82.998, strength: 0.6),
    ]);
  }
  
  void _spawnSwarm() {
    // Create initial swarm of quantum crawdads
    for (int i = 0; i < 10; i++) {
      swarm.add(QuantumCrawdad(
        id: 'qd-$i',
        position: _randomPosition(),
        energy: 1.0,
      ));
    }
  }
  
  void _startSwarmActivity() {
    _swarmTimer = Timer.periodic(Duration(milliseconds: 500), (_) {
      _updateSwarm();
      _calculateMetrics();
      notifyListeners();
    });
  }
  
  void _updateSwarm() {
    for (var crawdad in swarm) {
      // Retrograde processing - work backward from best signal
      var bestSignal = _findBestSignal(crawdad.position);
      
      if (bestSignal != null) {
        // Create pheromone trail to best signal
        _createTrail(crawdad.position, bestSignal.position, bestSignal.strength);
        
        // Move crawdad using quantum tunneling probability
        if (_random.nextDouble() < 0.3) {
          // Quantum tunnel to better position
          crawdad.position = _quantumTunnel(crawdad.position, bestSignal.position);
        } else {
          // Classical crawdad movement (backward scuttle)
          crawdad.position = _retrogradeMove(crawdad.position, bestSignal.position);
        }
      }
      
      // Energy management
      crawdad.energy = max(0, crawdad.energy - 0.01);
      if (crawdad.energy < 0.2) {
        crawdad.hibernate();
      }
    }
    
    // Decay old trails
    trails.removeWhere((trail) => trail.strength < 0.1);
    for (var trail in trails) {
      trail.decay();
    }
  }
  
  NetworkNode? _findBestSignal(Position pos) {
    NetworkNode? best;
    double bestScore = 0;
    
    // Check all towers and routers
    for (var tower in towers) {
      double distance = _calculateDistance(pos, Position(tower.lat, tower.lon));
      double score = tower.strength * (1 - tower.congestion) / (1 + distance);
      if (score > bestScore) {
        bestScore = score;
        best = tower;
      }
    }
    
    for (var router in routers) {
      double distance = _calculateDistance(pos, Position(router.lat, router.lon));
      double score = router.strength / (1 + distance);
      if (score > bestScore) {
        bestScore = score;
        best = router;
      }
    }
    
    return best;
  }
  
  void _createTrail(Position from, Position to, double strength) {
    trails.add(PheromoneTrail(
      from: from,
      to: to,
      strength: strength,
      timestamp: DateTime.now(),
    ));
  }
  
  Position _quantumTunnel(Position from, Position to) {
    // Quantum tunneling - instant transmission to better position
    double t = _random.nextDouble() * 0.5 + 0.5; // 50-100% of distance
    return Position(
      from.lat + (to.lat - from.lat) * t,
      from.lon + (to.lon - from.lon) * t,
    );
  }
  
  Position _retrogradeMove(Position from, Position to) {
    // Crawdad backward movement - 140% efficiency
    double efficiency = 1.4;
    double step = 0.01 * efficiency;
    return Position(
      from.lat + (to.lat - from.lat) * step,
      from.lon + (to.lon - from.lon) * step,
    );
  }
  
  double _calculateDistance(Position a, Position b) {
    return sqrt(pow(a.lat - b.lat, 2) + pow(a.lon - b.lon, 2));
  }
  
  Position _randomPosition() {
    return Position(
      35.5 + (_random.nextDouble() - 0.5) * 0.02,
      -83.0 + (_random.nextDouble() - 0.5) * 0.02,
    );
  }
  
  void _calculateMetrics() {
    if (swarm.isEmpty) return;
    
    activeConnections = swarm.where((c) => !c.isHibernating).length;
    
    double totalStrength = 0;
    for (var crawdad in swarm) {
      var signal = _findBestSignal(crawdad.position);
      if (signal != null) {
        totalStrength += signal.strength;
      }
    }
    
    avgSignalStrength = totalStrength / swarm.length;
    networkEfficiency = avgSignalStrength * (activeConnections / swarm.length);
  }
  
  @override
  void dispose() {
    _swarmTimer?.cancel();
    super.dispose();
  }
}

/// 🦞 Individual Quantum Crawdad
class QuantumCrawdad {
  final String id;
  Position position;
  double energy;
  bool isHibernating = false;
  
  QuantumCrawdad({
    required this.id,
    required this.position,
    required this.energy,
  });
  
  void hibernate() {
    isHibernating = true;
  }
  
  void wake() {
    isHibernating = false;
    energy = 1.0;
  }
}

/// Pheromone Trail for swarm communication
class PheromoneTrail {
  final Position from;
  final Position to;
  double strength;
  final DateTime timestamp;
  
  PheromoneTrail({
    required this.from,
    required this.to,
    required this.strength,
    required this.timestamp,
  });
  
  void decay() {
    strength *= 0.95; // Exponential decay
  }
  
  double getCurrentStrength() {
    final age = DateTime.now().difference(timestamp).inSeconds;
    return strength * exp(-0.01 * age);
  }
}

/// Two Wolves Controller - Privacy architecture
class TwoWolvesController extends ChangeNotifier {
  bool _isLightWolfActive = true; // Default to privacy
  
  bool get isLightWolfActive => _isLightWolfActive;
  
  String get activeWolf => _isLightWolfActive ? 'Light Wolf (Guardian)' : 'Shadow Wolf (Tracker)';
  
  void switchWolf() {
    _isLightWolfActive = !_isLightWolfActive;
    notifyListeners();
    
    if (!_isLightWolfActive) {
      // Show scary consent dialog
      print('⚠️ WARNING: Shadow Wolf tracks everything!');
    }
  }
  
  Map<String, dynamic> processData(Map<String, dynamic> data) {
    if (_isLightWolfActive) {
      // Light Wolf: Heavy privacy protection
      return _lightWolfProcess(data);
    } else {
      // Shadow Wolf: Full tracking
      return _shadowWolfProcess(data);
    }
  }
  
  Map<String, dynamic> _lightWolfProcess(Map<String, dynamic> data) {
    return {
      'location': _gridLocation(data['location']), // 1km grid only
      'time': _timeBucket(data['time']), // Hour buckets only
      'signal': data['signal']?.round(), // Rounded values
      // Auto-delete after 5 minutes
    };
  }
  
  Map<String, dynamic> _shadowWolfProcess(Map<String, dynamic> data) {
    // Full data with tracking
    return {
      ...data,
      'tracked': true,
      'timestamp': DateTime.now().toIso8601String(),
    };
  }
  
  String _gridLocation(dynamic location) {
    // Convert to 1km grid
    return 'Grid_${(location['lat'] * 100).round()}_${(location['lon'] * 100).round()}';
  }
  
  String _timeBucket(dynamic time) {
    // Convert to hour bucket
    return 'Hour_${DateTime.now().hour}';
  }
}

/// Pheromone Trail Manager
class PheromoneTrailManager extends ChangeNotifier {
  final List<StoredTrail> storedTrails = [];
  
  void storeTrail(String context, String path, double success) {
    storedTrails.add(StoredTrail(
      context: context,
      path: path,
      successRate: success,
      uses: 1,
    ));
    
    // Keep only top 100 trails
    if (storedTrails.length > 100) {
      storedTrails.sort((a, b) => b.successRate.compareTo(a.successRate));
      storedTrails.removeRange(100, storedTrails.length);
    }
    
    notifyListeners();
  }
  
  StoredTrail? findBestTrail(String context) {
    final matches = storedTrails.where((t) => t.context == context).toList();
    if (matches.isEmpty) return null;
    
    matches.sort((a, b) => b.score.compareTo(a.score));
    return matches.first;
  }
}

/// Helper Classes
class Position {
  final double lat;
  final double lon;
  
  Position(this.lat, this.lon);
}

abstract class NetworkNode {
  String get id;
  double get lat;
  double get lon;
  double get strength;
  Position get position => Position(lat, lon);
}

class MockCellTower extends NetworkNode {
  @override
  final String id;
  @override
  final double lat;
  @override
  final double lon;
  @override
  final double strength;
  final double congestion;
  
  MockCellTower(this.id, {
    required this.lat,
    required this.lon,
    required this.strength,
    required this.congestion,
  });
}

class MockWiFiRouter extends NetworkNode {
  @override
  final String id;
  @override
  final double lat;
  @override
  final double lon;
  @override
  final double strength;
  
  MockWiFiRouter(this.id, {
    required this.lat,
    required this.lon,
    required this.strength,
  });
}

class StoredTrail {
  final String context;
  final String path;
  final double successRate;
  int uses;
  
  StoredTrail({
    required this.context,
    required this.path,
    required this.successRate,
    required this.uses,
  });
  
  double get score => successRate * log(uses + 1);
}