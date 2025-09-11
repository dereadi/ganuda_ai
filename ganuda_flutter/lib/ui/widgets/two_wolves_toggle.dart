import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/quantum_crawdad_engine.dart';

class TwoWolvesToggle extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final controller = context.watch<TwoWolvesController>();
    
    return Container(
      margin: EdgeInsets.all(16),
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: controller.isLightWolfActive
              ? [Color(0xFF4169E1), Color(0xFF87CEEB)]
              : [Color(0xFF800020), Color(0xFFDC143C)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: controller.isLightWolfActive
                ? Colors.blue.withOpacity(0.3)
                : Colors.red.withOpacity(0.3),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '🐺',
                style: TextStyle(fontSize: 32),
              ),
              SizedBox(width: 16),
              Text(
                controller.activeWolf,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(width: 16),
              Text(
                '🐺',
                style: TextStyle(fontSize: 32),
              ),
            ],
          ),
          SizedBox(height: 12),
          
          // Toggle switch
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // Light Wolf option
              Expanded(
                child: GestureDetector(
                  onTap: controller.isLightWolfActive ? null : () => controller.switchWolf(),
                  child: Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: controller.isLightWolfActive
                          ? Colors.white.withOpacity(0.9)
                          : Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: controller.isLightWolfActive
                            ? Color(0xFFFFD700)
                            : Colors.transparent,
                        width: 3,
                      ),
                    ),
                    child: Column(
                      children: [
                        Icon(
                          Icons.shield,
                          color: controller.isLightWolfActive
                              ? Colors.blue
                              : Colors.grey,
                          size: 32,
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Guardian',
                          style: TextStyle(
                            color: controller.isLightWolfActive
                                ? Colors.black
                                : Colors.white60,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'Privacy First',
                          style: TextStyle(
                            color: controller.isLightWolfActive
                                ? Colors.black87
                                : Colors.white60,
                            fontSize: 10,
                          ),
                        ),
                        if (controller.isLightWolfActive)
                          Column(
                            children: [
                              SizedBox(height: 4),
                              Text(
                                '✓ 5-min memory',
                                style: TextStyle(fontSize: 9, color: Colors.green),
                              ),
                              Text(
                                '✓ No tracking',
                                style: TextStyle(fontSize: 9, color: Colors.green),
                              ),
                            ],
                          ),
                      ],
                    ),
                  ),
                ),
              ),
              
              SizedBox(width: 16),
              
              // Shadow Wolf option
              Expanded(
                child: GestureDetector(
                  onTap: !controller.isLightWolfActive ? null : () => _showWarningDialog(context, controller),
                  child: Container(
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: !controller.isLightWolfActive
                          ? Colors.black.withOpacity(0.9)
                          : Colors.black.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: !controller.isLightWolfActive
                            ? Colors.red
                            : Colors.transparent,
                        width: 3,
                      ),
                    ),
                    child: Column(
                      children: [
                        Icon(
                          Icons.visibility,
                          color: !controller.isLightWolfActive
                              ? Colors.red
                              : Colors.grey,
                          size: 32,
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Tracker',
                          style: TextStyle(
                            color: !controller.isLightWolfActive
                                ? Colors.white
                                : Colors.white60,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          'Full Features',
                          style: TextStyle(
                            color: !controller.isLightWolfActive
                                ? Colors.white
                                : Colors.white60,
                            fontSize: 10,
                          ),
                        ),
                        if (!controller.isLightWolfActive)
                          Column(
                            children: [
                              SizedBox(height: 4),
                              Text(
                                '⚠️ Tracks all',
                                style: TextStyle(fontSize: 9, color: Colors.orange),
                              ),
                              Text(
                                '⚠️ Remembers',
                                style: TextStyle(fontSize: 9, color: Colors.orange),
                              ),
                            ],
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
          
          SizedBox(height: 8),
          
          // Cherokee wisdom quote
          Text(
            '"Two wolves fight within us. Which wins? The one you feed."',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 11,
              fontStyle: FontStyle.italic,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
  
  void _showWarningDialog(BuildContext context, TwoWolvesController controller) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        backgroundColor: Color(0xFF800020),
        title: Row(
          children: [
            Icon(Icons.warning, color: Colors.orange, size: 32),
            SizedBox(width: 8),
            Text(
              'WARNING',
              style: TextStyle(color: Colors.white, fontSize: 24),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Shadow Wolf WILL:',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
            SizedBox(height: 10),
            _warningItem('Track your exact location continuously'),
            _warningItem('Remember all your network patterns'),
            _warningItem('Store your data permanently'),
            _warningItem('Share data with network providers'),
            _warningItem('Create detailed user profile'),
            SizedBox(height: 16),
            Text(
              'Are you SURE you want to feed the Shadow Wolf?',
              style: TextStyle(
                color: Colors.orange,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(
              'STAY WITH LIGHT WOLF',
              style: TextStyle(color: Colors.green),
            ),
          ),
          TextButton(
            onPressed: () {
              controller.switchWolf();
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Shadow Wolf activated. You can switch back anytime.'),
                  backgroundColor: Colors.red,
                  action: SnackBarAction(
                    label: 'UNDO',
                    textColor: Colors.white,
                    onPressed: () => controller.switchWolf(),
                  ),
                ),
              );
            },
            child: Text(
              'ACTIVATE SHADOW WOLF',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _warningItem(String text) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(Icons.arrow_right, color: Colors.orange, size: 16),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}