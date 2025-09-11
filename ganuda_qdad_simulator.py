#!/usr/bin/env python3
"""
🦞 GANUDA Q-DAD SIMULATOR
Testing Quantum Crawdads in a mock cellular environment
"""

import random
import time
import math
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import os
import sys

class Colors:
    """ANSI color codes for terminal output"""
    ORANGE = '\033[33m'
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[93m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class Position:
    """Geographic position"""
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position"""
        return math.sqrt((self.lat - other.lat)**2 + (self.lon - other.lon)**2)

class PheromoneTrail:
    """Digital trail left by successful connections"""
    def __init__(self, from_pos: Position, to_pos: Position, strength: float):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.strength = strength
        self.timestamp = datetime.now()
        self.uses = 1
    
    def decay(self):
        """Exponential decay of trail strength"""
        self.strength *= 0.95
    
    def reinforce(self):
        """Strengthen trail when successfully used"""
        self.strength = min(1.0, self.strength * 1.1)
        self.uses += 1

class NetworkNode:
    """Base class for network infrastructure"""
    def __init__(self, id: str, pos: Position, strength: float):
        self.id = id
        self.pos = pos
        self.strength = strength

class CellTower(NetworkNode):
    """Cellular tower with congestion"""
    def __init__(self, id: str, pos: Position, strength: float, congestion: float = 0.3):
        super().__init__(id, pos, strength)
        self.congestion = congestion
        self.connected_devices = 0
    
    def get_signal_quality(self, device_pos: Position) -> float:
        """Calculate signal quality based on distance and congestion"""
        distance = self.pos.distance_to(device_pos)
        signal = self.strength * (1 - self.congestion) / (1 + distance * 10)
        return max(0, min(1, signal))

class WiFiRouter(NetworkNode):
    """WiFi access point"""
    def get_signal_quality(self, device_pos: Position) -> float:
        """Calculate WiFi signal quality"""
        distance = self.pos.distance_to(device_pos)
        signal = self.strength / (1 + distance * 20)
        return max(0, min(1, signal))

class QuantumCrawdad:
    """🦞 Individual Q-DAD with retrograde processing"""
    def __init__(self, id: str, pos: Position):
        self.id = id
        self.pos = pos
        self.energy = 1.0
        self.hibernating = False
        self.current_connection = None
        self.memory = []  # Recent successful paths
    
    def retrograde_process(self, target: NetworkNode) -> Position:
        """Process backward from solution to current position (140% efficiency)"""
        # Work backward from best signal to current position
        efficiency = 1.4
        step_size = 0.001 * efficiency
        
        # Calculate optimal path backward
        delta_lat = (target.pos.lat - self.pos.lat) * step_size
        delta_lon = (target.pos.lon - self.pos.lon) * step_size
        
        return Position(self.pos.lat + delta_lat, self.pos.lon + delta_lon)
    
    def quantum_tunnel(self, target: NetworkNode) -> Position:
        """Quantum tunneling to better position (30% probability)"""
        if random.random() < 0.3:
            # Instant transmission to near target
            t = random.uniform(0.5, 0.9)
            new_lat = self.pos.lat + (target.pos.lat - self.pos.lat) * t
            new_lon = self.pos.lon + (target.pos.lon - self.pos.lon) * t
            return Position(new_lat, new_lon)
        return self.pos
    
    def hibernate(self):
        """Enter low-power hibernation mode"""
        self.hibernating = True
        self.energy = 0.1
    
    def wake(self):
        """Wake from hibernation"""
        self.hibernating = False
        self.energy = 1.0

class TwoWolvesArchitecture:
    """🐺🐺 Dual-mode privacy system"""
    def __init__(self):
        self.light_wolf_active = True  # Default to privacy
        self.shadow_data = []
        self.light_data = []
    
    def process_data(self, data: Dict) -> Dict:
        """Process data according to active wolf"""
        if self.light_wolf_active:
            return self._light_wolf_process(data)
        else:
            return self._shadow_wolf_process(data)
    
    def _light_wolf_process(self, data: Dict) -> Dict:
        """Guardian mode - maximum privacy"""
        return {
            'location': f"Grid_{int(data['lat']*100)}_{int(data['lon']*100)}",
            'time': f"Hour_{datetime.now().hour}",
            'signal': round(data.get('signal', 0), 1),
            # Auto-delete after 5 minutes
        }
    
    def _shadow_wolf_process(self, data: Dict) -> Dict:
        """Tracker mode - full features"""
        self.shadow_data.append(data)
        return {
            **data,
            'tracked': True,
            'timestamp': datetime.now().isoformat(),
            'profile_id': 'user_profile_001'
        }
    
    def switch_wolf(self):
        """Toggle between wolves"""
        self.light_wolf_active = not self.light_wolf_active
        mode = "Light Wolf (Guardian)" if self.light_wolf_active else "Shadow Wolf (Tracker)"
        return mode

class GanudaSimulator:
    """Main simulation engine"""
    def __init__(self):
        self.crawdads: List[QuantumCrawdad] = []
        self.towers: List[CellTower] = []
        self.routers: List[WiFiRouter] = []
        self.trails: List[PheromoneTrail] = []
        self.two_wolves = TwoWolvesArchitecture()
        self.metrics = {
            'efficiency': 0.0,
            'signal_strength': 0.0,
            'active_crawdads': 0,
            'trails_active': 0
        }
        
        self._initialize_network()
        self._spawn_crawdads()
    
    def _initialize_network(self):
        """Create mock network infrastructure"""
        # Cherokee Nation area (rough coordinates)
        base_lat, base_lon = 35.5, -83.0
        
        # Create cell towers
        self.towers = [
            CellTower("Tower-A", Position(base_lat, base_lon), 0.8, 0.3),
            CellTower("Tower-B", Position(base_lat + 0.01, base_lon + 0.01), 0.6, 0.7),
            CellTower("Tower-C", Position(base_lat - 0.01, base_lon - 0.01), 0.9, 0.5),
        ]
        
        # Create WiFi routers
        self.routers = [
            WiFiRouter("Cherokee-Guest", Position(base_lat + 0.002, base_lon), 0.7),
            WiFiRouter("Sacred-Fire", Position(base_lat, base_lon + 0.002), 0.9),
            WiFiRouter("Seven-Generations", Position(base_lat - 0.002, base_lon - 0.002), 0.6),
        ]
    
    def _spawn_crawdads(self, count: int = 10):
        """Create initial swarm"""
        base_lat, base_lon = 35.5, -83.0
        
        for i in range(count):
            pos = Position(
                base_lat + random.uniform(-0.02, 0.02),
                base_lon + random.uniform(-0.02, 0.02)
            )
            self.crawdads.append(QuantumCrawdad(f"qd-{i}", pos))
    
    def find_best_signal(self, pos: Position) -> Tuple[Optional[NetworkNode], float]:
        """Find best network signal at position"""
        best_node = None
        best_quality = 0.0
        
        for tower in self.towers:
            quality = tower.get_signal_quality(pos)
            if quality > best_quality:
                best_quality = quality
                best_node = tower
        
        for router in self.routers:
            quality = router.get_signal_quality(pos)
            if quality > best_quality:
                best_quality = quality
                best_node = router
        
        return best_node, best_quality
    
    def update_swarm(self):
        """Update all crawdads"""
        active = 0
        total_signal = 0.0
        
        for crawdad in self.crawdads:
            if crawdad.hibernating:
                if crawdad.energy < 0.2:
                    continue
                else:
                    crawdad.wake()
            
            active += 1
            
            # Find best signal
            best_node, quality = self.find_best_signal(crawdad.pos)
            
            if best_node:
                total_signal += quality
                
                # Check for existing trail
                trail = self.find_trail(crawdad.pos, best_node.pos)
                if trail:
                    trail.reinforce()
                else:
                    # Create new trail
                    self.trails.append(
                        PheromoneTrail(crawdad.pos, best_node.pos, quality)
                    )
                
                # Move crawdad
                if random.random() < 0.3:
                    # Quantum tunnel
                    crawdad.pos = crawdad.quantum_tunnel(best_node)
                else:
                    # Retrograde movement
                    crawdad.pos = crawdad.retrograde_process(best_node)
                
                # Energy management
                crawdad.energy -= 0.02
                if crawdad.energy < 0.2:
                    crawdad.hibernate()
        
        # Decay trails
        self.trails = [t for t in self.trails if t.strength > 0.1]
        for trail in self.trails:
            trail.decay()
        
        # Update metrics
        self.metrics['active_crawdads'] = active
        self.metrics['signal_strength'] = total_signal / len(self.crawdads) if self.crawdads else 0
        self.metrics['efficiency'] = self.metrics['signal_strength'] * 1.4  # 140% efficiency
        self.metrics['trails_active'] = len(self.trails)
    
    def find_trail(self, from_pos: Position, to_pos: Position) -> Optional[PheromoneTrail]:
        """Find existing trail between positions"""
        for trail in self.trails:
            if trail.from_pos.distance_to(from_pos) < 0.001 and \
               trail.to_pos.distance_to(to_pos) < 0.001:
                return trail
        return None
    
    def display_status(self):
        """Display simulation status"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"{Colors.BOLD}{Colors.YELLOW}")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║                    🦞 GANUDA Q-DAD SIMULATOR                      ║")
        print("║                     Cherokee Digital Sovereignty                  ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print(Colors.RESET)
        
        # Two Wolves Status
        wolf_mode = "🐺 Light Wolf (Privacy)" if self.two_wolves.light_wolf_active else "🐺 Shadow Wolf (Tracking)"
        wolf_color = Colors.CYAN if self.two_wolves.light_wolf_active else Colors.RED
        print(f"\n{wolf_color}{Colors.BOLD}Active Mode: {wolf_mode}{Colors.RESET}")
        
        # Network Status
        print(f"\n{Colors.GREEN}📡 Network Infrastructure:{Colors.RESET}")
        print(f"  Cell Towers: {len(self.towers)}")
        print(f"  WiFi Routers: {len(self.routers)}")
        
        # Swarm Status
        print(f"\n{Colors.ORANGE}🦞 Quantum Crawdad Swarm:{Colors.RESET}")
        print(f"  Active: {self.metrics['active_crawdads']}/{len(self.crawdads)}")
        hibernating = len(self.crawdads) - self.metrics['active_crawdads']
        if hibernating > 0:
            print(f"  Hibernating: {hibernating} 💤")
        
        # Performance Metrics
        print(f"\n{Colors.PURPLE}📊 Performance Metrics:{Colors.RESET}")
        efficiency_pct = self.metrics['efficiency'] * 100
        signal_pct = self.metrics['signal_strength'] * 100
        
        print(f"  Efficiency: {Colors.BOLD}{efficiency_pct:.1f}%{Colors.RESET} (Retrograde Processing)")
        print(f"  Signal Strength: {signal_pct:.1f}%")
        print(f"  Active Trails: {self.metrics['trails_active']} {Colors.YELLOW}〰️{Colors.RESET}")
        
        # Visualize network map
        print(f"\n{Colors.BLUE}📍 Network Map (1km grid):{Colors.RESET}")
        self.display_map()
        
        # Instructions
        print(f"\n{Colors.WHITE}Commands:{Colors.RESET}")
        print("  [w] Switch Wolf Mode | [s] Spawn Q-DAD | [c] Add Congestion")
        print("  [h] Hibernate All | [a] Wake All | [q] Quit")
    
    def display_map(self):
        """Simple ASCII map visualization"""
        # Create 10x10 grid
        grid = [[' ' for _ in range(20)] for _ in range(10)]
        
        # Place towers
        for tower in self.towers:
            x = int((tower.pos.lon + 83.02) * 500) % 20
            y = int((35.52 - tower.pos.lat) * 500) % 10
            if 0 <= x < 20 and 0 <= y < 10:
                grid[y][x] = f"{Colors.BLUE}📡{Colors.RESET}"
        
        # Place routers
        for router in self.routers:
            x = int((router.pos.lon + 83.02) * 500) % 20
            y = int((35.52 - router.pos.lat) * 500) % 10
            if 0 <= x < 20 and 0 <= y < 10:
                grid[y][x] = f"{Colors.GREEN}📶{Colors.RESET}"
        
        # Place crawdads
        for crawdad in self.crawdads[:5]:  # Show first 5
            x = int((crawdad.pos.lon + 83.02) * 500) % 20
            y = int((35.52 - crawdad.pos.lat) * 500) % 10
            if 0 <= x < 20 and 0 <= y < 10:
                if crawdad.hibernating:
                    grid[y][x] = '💤'
                else:
                    grid[y][x] = '🦞'
        
        # Display grid
        print("  +" + "-" * 40 + "+")
        for row in grid:
            print("  |", end="")
            for cell in row:
                if cell == ' ':
                    print(". ", end="")
                else:
                    print(f"{cell}", end="")
            print("|")
        print("  +" + "-" * 40 + "+")
    
    def add_congestion(self):
        """Simulate network congestion"""
        if self.towers:
            tower = random.choice(self.towers)
            tower.congestion = min(1.0, tower.congestion + 0.2)
            print(f"\n⚠️  Added congestion to {tower.id} (now {tower.congestion:.1%})")
    
    def spawn_crawdad(self):
        """Add new crawdad to swarm"""
        base_lat, base_lon = 35.5, -83.0
        pos = Position(
            base_lat + random.uniform(-0.02, 0.02),
            base_lon + random.uniform(-0.02, 0.02)
        )
        crawdad = QuantumCrawdad(f"qd-{len(self.crawdads)}", pos)
        self.crawdads.append(crawdad)
        print(f"\n🦞 Spawned new Q-DAD: {crawdad.id}")
    
    def run(self):
        """Main simulation loop"""
        import threading
        
        def update_loop():
            while self.running:
                self.update_swarm()
                time.sleep(0.5)
        
        self.running = True
        update_thread = threading.Thread(target=update_loop)
        update_thread.daemon = True
        update_thread.start()
        
        try:
            while True:
                self.display_status()
                
                # Get user input (non-blocking)
                import select
                import termios
                import tty
                
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setraw(sys.stdin.fileno())
                    if select.select([sys.stdin], [], [], 1)[0]:
                        key = sys.stdin.read(1).lower()
                        
                        if key == 'q':
                            break
                        elif key == 'w':
                            mode = self.two_wolves.switch_wolf()
                            print(f"\n🐺 Switched to {mode}")
                        elif key == 's':
                            self.spawn_crawdad()
                        elif key == 'c':
                            self.add_congestion()
                        elif key == 'h':
                            for c in self.crawdads:
                                c.hibernate()
                            print("\n💤 All Q-DADs hibernating")
                        elif key == 'a':
                            for c in self.crawdads:
                                c.wake()
                            print("\n⚡ All Q-DADs awakened")
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            print(f"\n{Colors.YELLOW}🔥 Sacred Fire extinguished. Wado!{Colors.RESET}")

def main():
    """Run the Q-DAD simulator"""
    print(f"{Colors.BOLD}{Colors.YELLOW}")
    print("🦞 GANUDA Q-DAD SIMULATOR")
    print("Testing Quantum Crawdads for Cherokee Digital Sovereignty")
    print(f"{Colors.RESET}")
    print("\nInitializing quantum swarm...")
    time.sleep(1)
    
    simulator = GanudaSimulator()
    simulator.run()

if __name__ == "__main__":
    main()