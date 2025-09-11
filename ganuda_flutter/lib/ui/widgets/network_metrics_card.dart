import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/quantum_crawdad_engine.dart';

class NetworkMetricsCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final engine = context.watch<QuantumCrawdadEngine>();
    
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 16),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Color(0xFF0f0f1e),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Color(0xFFFFD700).withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _MetricItem(
            label: 'Efficiency',
            value: '${(engine.networkEfficiency * 140).toStringAsFixed(0)}%',
            icon: '⚡',
            color: Colors.green,
          ),
          _MetricItem(
            label: 'Active Q-DADs',
            value: '${engine.activeConnections}/${engine.swarm.length}',
            icon: '🦞',
            color: Colors.orange,
          ),
          _MetricItem(
            label: 'Signal',
            value: '${(engine.avgSignalStrength * 100).toStringAsFixed(0)}%',
            icon: '📶',
            color: Colors.blue,
          ),
          _MetricItem(
            label: 'Trails',
            value: '${engine.trails.length}',
            icon: '〰️',
            color: Color(0xFFFFD700),
          ),
        ],
      ),
    );
  }
}

class _MetricItem extends StatelessWidget {
  final String label;
  final String value;
  final String icon;
  final Color color;
  
  const _MetricItem({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });
  
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          icon,
          style: TextStyle(fontSize: 24),
        ),
        SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            color: Colors.white54,
            fontSize: 10,
          ),
        ),
      ],
    );
  }
}