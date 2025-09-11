import 'package:flutter/material.dart';
import 'package:device_preview/device_preview.dart';
import 'package:provider/provider.dart';
import 'core/quantum_crawdad_engine.dart';
import 'ui/screens/home_screen.dart';
import 'ui/theme/ganuda_theme.dart';

void main() {
  runApp(
    DevicePreview(
      enabled: true, // Enable to test on multiple mock devices
      devices: [
        ...Devices.ios.all,
        ...Devices.android.all,
      ],
      builder: (context) => GanudaApp(),
    ),
  );
}

class GanudaApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => QuantumCrawdadEngine()),
        ChangeNotifierProvider(create: (_) => TwoWolvesController()),
        ChangeNotifierProvider(create: (_) => PheromoneTrailManager()),
      ],
      child: MaterialApp(
        title: 'ᎦᏅᏓ Ganuda',
        debugShowCheckedModeBanner: false,
        useInheritedMediaQuery: true,
        locale: DevicePreview.locale(context),
        builder: DevicePreview.appBuilder,
        theme: GanudaTheme.lightTheme,
        darkTheme: GanudaTheme.darkTheme,
        home: HomeScreen(),
      ),
    );
  }
}