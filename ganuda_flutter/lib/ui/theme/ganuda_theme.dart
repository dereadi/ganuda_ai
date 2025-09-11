import 'package:flutter/material.dart';

class GanudaTheme {
  // Cherokee-inspired colors
  static const Color earthBrown = Color(0xFF8B4513);
  static const Color skyBlue = Color(0xFF4169E1);
  static const Color sacredGold = Color(0xFFFFD700);
  static const Color lightWolfWhite = Color(0xFFFFFFFF);
  static const Color shadowWolfBurgundy = Color(0xFF800020);
  static const Color darkBackground = Color(0xFF1a1a2e);
  static const Color darkerBackground = Color(0xFF0f0f1e);
  
  static ThemeData get lightTheme {
    return ThemeData(
      primaryColor: earthBrown,
      scaffoldBackgroundColor: Colors.grey[100],
      colorScheme: ColorScheme.light(
        primary: earthBrown,
        secondary: sacredGold,
        surface: Colors.white,
        background: Colors.grey[100]!,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: earthBrown,
        elevation: 0,
        centerTitle: true,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: earthBrown,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        ),
      ),
      textTheme: TextTheme(
        headlineLarge: TextStyle(
          color: earthBrown,
          fontSize: 32,
          fontWeight: FontWeight.bold,
        ),
        headlineMedium: TextStyle(
          color: earthBrown,
          fontSize: 24,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: TextStyle(
          color: Colors.black87,
          fontSize: 16,
        ),
        bodyMedium: TextStyle(
          color: Colors.black87,
          fontSize: 14,
        ),
      ),
    );
  }
  
  static ThemeData get darkTheme {
    return ThemeData(
      primaryColor: sacredGold,
      scaffoldBackgroundColor: darkBackground,
      colorScheme: ColorScheme.dark(
        primary: sacredGold,
        secondary: earthBrown,
        surface: darkerBackground,
        background: darkBackground,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: darkerBackground,
        elevation: 0,
        centerTitle: true,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: earthBrown,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        ),
      ),
      textTheme: TextTheme(
        headlineLarge: TextStyle(
          color: sacredGold,
          fontSize: 32,
          fontWeight: FontWeight.bold,
        ),
        headlineMedium: TextStyle(
          color: sacredGold,
          fontSize: 24,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: TextStyle(
          color: Colors.white,
          fontSize: 16,
        ),
        bodyMedium: TextStyle(
          color: Colors.white70,
          fontSize: 14,
        ),
      ),
    );
  }
}