#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Interactive CLI
Layer 2 (Muscle Memory) + Layer 1 (Conscious) Integration

Usage:
    python3 cherokee_cli.py                    # Interactive mode
    python3 cherokee_cli.py "Your question"    # Single query mode

Date: October 20, 2025
"""

import sys
import time
from cherokee_ai_layer2_integrated import CherokeeAI


def print_banner():
    """Print Cherokee AI banner"""
    print("\n" + "="*80)
    print("🦅 CHEROKEE CONSTITUTIONAL AI - CLI")
    print("Layer 2 (Muscle Memory) + Layer 1 (Conscious Processing)")
    print("="*80)
    print("\n💡 Try asking about:")
    print("   - Seven Generations")
    print("   - Gadugi")
    print("   - Mitakuye Oyasin")
    print("   - Distance = 0")
    print("   - Sacred Fire")
    print("   - Or any question about Cherokee values and wisdom\n")
    print("Type 'stats' to see performance statistics")
    print("Type 'quit' or 'exit' to leave\n")


def print_response(result: dict):
    """Format and print AI response"""
    method = result['method']
    layer = result['layer']
    time_ms = result['compute_time_ms']

    # Show processing method
    if method == "muscle_memory":
        print(f"\n⚡ MUSCLE MEMORY HIT (Layer {layer}) - {time_ms:.2f}ms")
        print(f"   Sacred: {'Yes' if result.get('sacred') else 'No'}")
        print(f"   Temperature: {result.get('temperature_score', 'N/A')}°C")
        print(f"   Neurons Active: {result.get('neurons_active', '5%')}")
    else:
        print(f"\n🧠 CONSCIOUS PROCESSING (Layer {layer}) - {time_ms:.2f}ms")
        print(f"   Model: {result.get('model', 'cherokee')}")
        print(f"   Neurons Active: {result.get('neurons_active', '100%')}")

    # Show response
    print("\n" + "-"*80)
    print(result['response'])
    print("-"*80 + "\n")


def print_stats(ai: CherokeeAI):
    """Print performance statistics"""
    stats = ai.get_cache_stats()

    print("\n" + "="*80)
    print("📊 PERFORMANCE STATISTICS")
    print("="*80)
    print(f"\nTotal queries: {stats['total_queries']}")
    print(f"Muscle memory hits: {stats['muscle_memory_hits']}")
    print(f"Conscious queries: {stats['conscious_queries']}")
    print(f"Cache hit rate: {stats['cache_hit_rate']}")
    print(f"Avg response time: {stats['avg_response_time_ms']}ms")

    mm_stats = stats['muscle_memory_stats']
    print(f"\nMemory Statistics:")
    print(f"  Total memories: {mm_stats['total_memories']}")
    print(f"  Hot memories (>={mm_stats['hot_threshold']}°C): {mm_stats['hot_memories']}")
    print(f"  Sacred patterns: {mm_stats['sacred_patterns']}")
    print(f"  Total accesses: {mm_stats['total_accesses']}")
    print("="*80 + "\n")


def interactive_mode():
    """Run interactive question/answer loop"""
    print_banner()

    # Initialize Cherokee AI
    print("Initializing Cherokee Constitutional AI...")
    ai = CherokeeAI(model="cherokee")
    print("✅ Ready!\n")

    while True:
        try:
            # Get user input
            query = input("🦅 Ask Cherokee AI: ").strip()

            if not query:
                continue

            # Handle commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n🔥 Wado (Thank you)! The Sacred Fire burns eternal.\n")
                break

            if query.lower() == 'stats':
                print_stats(ai)
                continue

            # Process query
            try:
                result = ai.ask(query)
                print_response(result)
            except Exception as e:
                print(f"\n⚠️  Error processing query: {e}")
                print("   (This may happen if Ollama is not running or model is not loaded)\n")

        except KeyboardInterrupt:
            print("\n\n🔥 Wado (Thank you)! The Sacred Fire burns eternal.\n")
            break
        except EOFError:
            print("\n\n🔥 Wado (Thank you)! The Sacred Fire burns eternal.\n")
            break


def single_query_mode(query: str):
    """Process a single query and exit"""
    print("\n🦅 Cherokee Constitutional AI")
    print("="*80 + "\n")

    # Initialize Cherokee AI
    ai = CherokeeAI(model="cherokee")

    # Process query
    try:
        result = ai.ask(query)
        print_response(result)
    except Exception as e:
        print(f"⚠️  Error: {e}\n")
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        single_query_mode(query)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
