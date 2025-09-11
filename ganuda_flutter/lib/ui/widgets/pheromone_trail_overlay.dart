import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/quantum_crawdad_engine.dart';

class PheromoneTrailOverlay extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final engine = context.watch<QuantumCrawdadEngine>();
    
    return CustomPaint(
      painter: TrailPainter(trails: engine.trails),
      child: Container(),
    );
  }
}

class TrailPainter extends CustomPainter {
  final List<PheromoneTrail> trails;
  
  TrailPainter({required this.trails});
  
  @override
  void paint(Canvas canvas, Size size) {
    for (var trail in trails) {
      final paint = Paint()
        ..color = Color(0xFFFFD700).withOpacity(trail.getCurrentStrength() * 0.5)
        ..strokeWidth = trail.getCurrentStrength() * 3
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;
      
      // Convert positions to screen coordinates
      final startX = ((trail.from.lon + 83.0) * 50000) % size.width;
      final startY = ((35.5 - trail.from.lat) * 50000) % size.height;
      final endX = ((trail.to.lon + 83.0) * 50000) % size.width;
      final endY = ((35.5 - trail.to.lat) * 50000) % size.height;
      
      // Draw trail as curved path (like crawdad movement)
      final path = Path();
      path.moveTo(startX, startY);
      
      // Create a curved path (retrograde crawdad style)
      final controlX = (startX + endX) / 2 + (endY - startY) * 0.2;
      final controlY = (startY + endY) / 2 - (endX - startX) * 0.2;
      
      path.quadraticBezierTo(controlX, controlY, endX, endY);
      
      canvas.drawPath(path, paint);
      
      // Draw pheromone particles along the trail
      if (trail.getCurrentStrength() > 0.3) {
        _drawPheromoneParticles(canvas, startX, startY, endX, endY, trail.getCurrentStrength());
      }
    }
  }
  
  void _drawPheromoneParticles(Canvas canvas, double x1, double y1, double x2, double y2, double strength) {
    final particlePaint = Paint()
      ..color = Color(0xFFFFD700).withOpacity(strength * 0.7)
      ..style = PaintingStyle.fill;
    
    // Draw 3-5 particles along the trail
    for (int i = 1; i <= 3; i++) {
      final t = i / 4.0;
      final x = x1 + (x2 - x1) * t;
      final y = y1 + (y2 - y1) * t;
      
      canvas.drawCircle(
        Offset(x, y),
        strength * 2,
        particlePaint,
      );
    }
  }
  
  @override
  bool shouldRepaint(TrailPainter oldDelegate) => true;
}