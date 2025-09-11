import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/quantum_crawdad_engine.dart';
import '../widgets/crawdad_swarm_visualizer.dart';
import '../widgets/two_wolves_toggle.dart';
import '../widgets/network_metrics_card.dart';
import '../widgets/pheromone_trail_overlay.dart';

class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF1a1a2e),
      appBar: AppBar(
        title: Row(
          children: [
            Text(
              'ᎦᏅᏓ',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Color(0xFFFFD700),
              ),
            ),
            SizedBox(width: 10),
            Text(
              'GANUDA',
              style: TextStyle(
                fontSize: 20,
                color: Colors.white70,
              ),
            ),
          ],
        ),
        backgroundColor: Color(0xFF0f0f1e),
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.info_outline, color: Color(0xFFFFD700)),
            onPressed: () => _showAboutDialog(context),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Two Wolves Toggle
            TwoWolvesToggle(),
            
            // Network Metrics
            NetworkMetricsCard(),
            
            // Main Swarm Visualization
            Expanded(
              child: Container(
                margin: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Color(0xFF0f0f1e),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: Color(0xFF8B4513),
                    width: 2,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Color(0xFFFFD700).withOpacity(0.1),
                      blurRadius: 20,
                      spreadRadius: 5,
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(18),
                  child: Stack(
                    children: [
                      // Background grid
                      _buildGridBackground(),
                      
                      // Pheromone trails
                      PheromoneTrailOverlay(),
                      
                      // Crawdad swarm
                      CrawdadSwarmVisualizer(),
                      
                      // Legend
                      _buildLegend(),
                    ],
                  ),
                ),
              ),
            ),
            
            // Action buttons
            _buildActionButtons(context),
          ],
        ),
      ),
    );
  }
  
  Widget _buildGridBackground() {
    return CustomPaint(
      painter: GridPainter(),
      child: Container(),
    );
  }
  
  Widget _buildLegend() {
    return Positioned(
      top: 10,
      left: 10,
      child: Container(
        padding: EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.black87,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _legendItem('🦞', 'Q-DAD (Active)', Colors.orange),
            _legendItem('💤', 'Q-DAD (Hibernating)', Colors.grey),
            _legendItem('📡', 'Cell Tower', Colors.blue),
            _legendItem('📶', 'WiFi Router', Colors.green),
            _legendItem('〰️', 'Pheromone Trail', Color(0xFFFFD700)),
          ],
        ),
      ),
    );
  }
  
  Widget _legendItem(String icon, String label, Color color) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Text(icon, style: TextStyle(fontSize: 16)),
          SizedBox(width: 8),
          Text(
            label,
            style: TextStyle(color: color, fontSize: 12),
          ),
        ],
      ),
    );
  }
  
  Widget _buildActionButtons(BuildContext context) {
    final engine = context.watch<QuantumCrawdadEngine>();
    
    return Container(
      padding: EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          ElevatedButton.icon(
            onPressed: () => _addCrawdad(context),
            icon: Icon(Icons.add),
            label: Text('Spawn Q-DAD'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Color(0xFF8B4513),
            ),
          ),
          ElevatedButton.icon(
            onPressed: () => _simulateCongestion(context),
            icon: Icon(Icons.warning),
            label: Text('Add Congestion'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Color(0xFFDC143C),
            ),
          ),
          ElevatedButton.icon(
            onPressed: () => _wakeAllCrawdads(context),
            icon: Icon(Icons.flash_on),
            label: Text('Wake All'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Color(0xFFFFD700),
              foregroundColor: Colors.black,
            ),
          ),
        ],
      ),
    );
  }
  
  void _addCrawdad(BuildContext context) {
    final engine = context.read<QuantumCrawdadEngine>();
    // Add implementation
  }
  
  void _simulateCongestion(BuildContext context) {
    final engine = context.read<QuantumCrawdadEngine>();
    // Add congestion to random tower
  }
  
  void _wakeAllCrawdads(BuildContext context) {
    final engine = context.read<QuantumCrawdadEngine>();
    for (var crawdad in engine.swarm) {
      crawdad.wake();
    }
  }
  
  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF1a1a2e),
        title: Text(
          'ᎦᏅᏓ GANUDA',
          style: TextStyle(color: Color(0xFFFFD700)),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Cherokee Digital Sovereignty',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 10),
            Text(
              'Named for Major Ridge - "The Man Who Walks on Mountaintops"',
              style: TextStyle(color: Colors.white70),
            ),
            SizedBox(height: 10),
            Text(
              '🦞 Quantum Crawdads: Retrograde processing at 140% efficiency',
              style: TextStyle(color: Colors.white70),
            ),
            SizedBox(height: 5),
            Text(
              '🐺🐺 Two Wolves: You choose privacy or convenience',
              style: TextStyle(color: Colors.white70),
            ),
            SizedBox(height: 5),
            Text(
              '🔥 Sacred Fire Priority: 1,353',
              style: TextStyle(color: Color(0xFFFFD700)),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              'Wado',
              style: TextStyle(color: Color(0xFFFFD700)),
            ),
          ),
        ],
      ),
    );
  }
}

class GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white10
      ..strokeWidth = 0.5
      ..style = PaintingStyle.stroke;
    
    // Draw grid
    const gridSize = 30.0;
    for (double x = 0; x < size.width; x += gridSize) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += gridSize) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }
  
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}