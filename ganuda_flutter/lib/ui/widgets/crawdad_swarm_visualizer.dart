import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:math';
import '../../core/quantum_crawdad_engine.dart';

class CrawdadSwarmVisualizer extends StatefulWidget {
  @override
  _CrawdadSwarmVisualizerState createState() => _CrawdadSwarmVisualizerState();
}

class _CrawdadSwarmVisualizerState extends State<CrawdadSwarmVisualizer>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late AnimationController _moveController;
  
  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: Duration(seconds: 2),
      vsync: this,
    )..repeat(reverse: true);
    
    _moveController = AnimationController(
      duration: Duration(milliseconds: 500),
      vsync: this,
    )..repeat();
  }
  
  @override
  void dispose() {
    _pulseController.dispose();
    _moveController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    final engine = context.watch<QuantumCrawdadEngine>();
    
    return LayoutBuilder(
      builder: (context, constraints) {
        return Stack(
          children: [
            // Draw cell towers
            ...engine.towers.map((tower) => _buildTower(tower, constraints)),
            
            // Draw WiFi routers
            ...engine.routers.map((router) => _buildRouter(router, constraints)),
            
            // Draw crawdads
            ...engine.swarm.map((crawdad) => _buildCrawdad(crawdad, constraints)),
          ],
        );
      },
    );
  }
  
  Widget _buildCrawdad(QuantumCrawdad crawdad, BoxConstraints constraints) {
    // Convert lat/lon to screen coordinates
    final x = ((crawdad.position.lon + 83.0) * 50000) % constraints.maxWidth;
    final y = ((35.5 - crawdad.position.lat) * 50000) % constraints.maxHeight;
    
    return AnimatedPositioned(
      duration: Duration(milliseconds: 500),
      left: x - 15,
      top: y - 15,
      child: AnimatedBuilder(
        animation: _pulseController,
        builder: (context, child) {
          final scale = crawdad.isHibernating 
              ? 0.8 
              : 1.0 + (_pulseController.value * 0.2);
          
          return Transform.scale(
            scale: scale,
            child: Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: crawdad.isHibernating 
                    ? Colors.grey.withOpacity(0.5)
                    : Colors.orange.withOpacity(0.8),
                boxShadow: crawdad.isHibernating ? [] : [
                  BoxShadow(
                    color: Colors.orange.withOpacity(0.5),
                    blurRadius: 10,
                    spreadRadius: 2,
                  ),
                ],
              ),
              child: Center(
                child: Text(
                  crawdad.isHibernating ? '💤' : '🦞',
                  style: TextStyle(fontSize: 16),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
  
  Widget _buildTower(MockCellTower tower, BoxConstraints constraints) {
    final x = ((tower.lon + 83.0) * 50000) % constraints.maxWidth;
    final y = ((35.5 - tower.lat) * 50000) % constraints.maxHeight;
    
    return Positioned(
      left: x - 20,
      top: y - 20,
      child: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.blue.withOpacity(0.3),
          border: Border.all(color: Colors.blue, width: 2),
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            Text('📡', style: TextStyle(fontSize: 20)),
            // Signal strength indicator
            if (tower.congestion > 0.5)
              Positioned(
                top: 0,
                right: 0,
                child: Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.red,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildRouter(MockWiFiRouter router, BoxConstraints constraints) {
    final x = ((router.lon + 83.0) * 50000) % constraints.maxWidth;
    final y = ((35.5 - router.lat) * 50000) % constraints.maxHeight;
    
    return Positioned(
      left: x - 15,
      top: y - 15,
      child: Container(
        width: 30,
        height: 30,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.green.withOpacity(0.3),
          border: Border.all(color: Colors.green, width: 2),
        ),
        child: Center(
          child: Text('📶', style: TextStyle(fontSize: 16)),
        ),
      ),
    );
  }
}