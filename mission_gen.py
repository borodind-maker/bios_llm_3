"""
smartbees/app/intelligence/mission_generator.py

🧠 LLM + AI Brain Integration Module
Military scenario generator using LLM for strategy and RL for execution.

Architecture:
    LLM Layer (Strategic) → Generates tactical scenarios based on classic military doctrines.
    RL Layer (Tactical) → Executes precise motor control and risk assessment.
    Validation Layer → Physics + Risk assessment.
"""

import json
import logging
import asyncio
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field

# Import LLM components
try:
    from smartbees.app.llm import LLMEngine, PromptBuilder, ContextManager
    from smartbees.app.llm.context_manager import ContextPriority
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logging.warning("LLM module not available - using mock mode")

# Import AI components
try:
    from smartbees.ai import OnlineLearner
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logging.warning("AI module not available")

# Import Brain Analytic (if available)
try:
    from smartbees.app.brain_analytic import AnalyticCore
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False

try:
    from smartbees.app.weather.weather_service import WeatherService
except ImportError:
    logging.warning("WeatherService not available")
    WeatherService = None


@dataclass
class TacticalScenario:
    """Structure of a single tactical scenario."""
    id: int
    name: str
    concept: str
    modules_used: List[str]
    execution_steps: List[str]
    success_probability: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    casualties_estimated: str
    advantages: List[str]
    vulnerabilities: List[str]
    distance_km: float = 0.0
    drones_required: int = 1
    time_limit_minutes: int = 60
    physically_feasible: bool = True
    validation_notes: str = ""
    ai_risk_score: float = 0.0


@dataclass
class MissionBrief:
    """Mission description provided by the operator."""
    objective: str  # 'deep_penetration_strike', 'reconnaissance', etc.
    target_coords: Tuple[float, float]  # (lat, lon)
    available_drones: int
    battery_percent: float
    time_limit: int  # minutes
    weather_condition: str = 'clear'
    wind_speed: float = 0.0
    known_threats: List[str] = field(default_factory=list)
    constraints: Dict = field(default_factory=dict)


class MissionGenerator:
    """
    Military Scenario Generator.
    
    Flow:
    1. Operator input → Mission brief
    2. Context aggregation → Sensors + Intel + History
    3. Strategy Selection → Sun Tzu / Liddell Hart / Clausewitz
    4. LLM generation → 5-10 scenarios
    5. Physics validation → Energy, time, aerodynamics
    6. AI risk assessment → RL model evaluation
    7. Ranking → Best scenarios first
    8. Operator approval → Select & execute
    """
    
    def __init__(
        self,
        llm_model_path: str = "/data/local/tmp/llm/gemma-3n-e2b.task",
        use_mock_llm: bool = False
    ):
        """
        Initialize the generator.
        
        Args:
            llm_model_path: Path to the LLM model on the device.
            use_mock_llm: If True, uses mock responses for testing.
        """
        self.logger = logging.getLogger(__name__)
        self.use_mock = use_mock_llm or not LLM_AVAILABLE

        # Initialize LLM (if available)
        if LLM_AVAILABLE and not self.use_mock:
            try:
                self.llm = LLMEngine(
                    model_path=llm_model_path,
                    temperature=0.8,  # Higher creativity for tactics
                    max_tokens=512,
                    top_k=40
                )
                self.context = ContextManager(max_tokens=2048)
                self.prompt_builder = PromptBuilder(safety_mode=False)
                self.logger.info("✅ LLM Engine initialized")
            except Exception as e:
                self.logger.error(f"Failed to init LLM: {e}")
                self.use_mock = True

        # Initialize AI Brain (if available)
        if AI_AVAILABLE:
            self.learner = OnlineLearner({
                'learning_rate': 0.001,
                'buffer_capacity': 2000,
                'min_samples': 64
            })
            self.logger.info("✅ AI Learner initialized")
        else:
            self.learner = None

        # Initialize Brain Analytic (if available)
        if BRAIN_AVAILABLE:
            try:
                self.analytics = AnalyticCore()
                self.logger.info("✅ Brain Analytic initialized")
            except:
                self.analytics = None
        else:
            self.analytics = None
        
        # Modules available in the system
        self.available_modules = [
            'LineCharge',           # Power line charging
            'BlockchainHiveMind',   # Collective learning
            'AntiSpoofing',         # Navigation without GPS
            'SwarmLink',            # Mesh network
            'TrojanTransport',      # Electronic warfare / Payload delivery
            'VisionFusion',         # Computer vision
            'WeatherService',       # Weather data
            'ElevationService',     # Terrain maps
            'PhantomDecoy',         # Deception tactics
            'PhantomDecoy',         # Deception tactics
            'SwarmManager'          # Swarm coordination
        ]
        
        # Initialize Weather Service
        try:
            self.weather_service = WeatherService() if WeatherService else None
        except Exception as e:
            self.logger.error(f"Failed to init WeatherService: {e}")
            self.weather_service = None

    # -----------------------------------------------------------
    # STRATEGIC DOCTRINES LOADING & SELECTION
    # -----------------------------------------------------------

    def _load_json_db(self, filename: str) -> dict:
        """Helper to load JSON strategy databases safely."""
        # Try relative path first, then absolute Android path
        paths = [
            f"data/strategies/{filename}",           # Correct project root path
            f"smartbees/data/strategies/{filename}", # Legacy path
            f"/data/local/tmp/smartbees/data/strategies/{filename}",
            os.path.join(os.path.dirname(__file__), "../../../data/strategies", filename) # Relative to this file
        ]
        
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.logger.info(f"📚 Loaded strategy DB: {path}")
                        return json.load(f)
                except Exception as e:
                    self.logger.error(f"Failed to load {filename}: {e}")
                    return {}
        
        self.logger.warning(f"Strategy DB not found: {filename}")
        return {}

    def _load_sun_tzu_strategies(self) -> dict:
        """Loads Sun Tzu knowledge base."""
        return self._load_json_db("sun_tzu_drone_tactics.json")

    def _load_stratagems(self) -> list:
        """Loads 36 Stratagems database."""
        data = self._load_json_db("stratagems_db.json")
        return data.get("stratagems", [])

    def _load_liddell_hart(self) -> dict:
        """Loads Liddell Hart's Indirect Approach database."""
        return self._load_json_db("liddell_hart_strategy.json")

    def _load_corporate_doctrine(self) -> dict:
        """Loads Corporate Warfare doctrines."""
        return self._load_json_db("corporate_warfare_doctrine.json")

    def _get_tactical_wisdom(self, mission_brief: MissionBrief) -> str:
        """Selects Sun Tzu wisdom relevant to the specific situation."""
        sun_tzu_db = self._load_sun_tzu_strategies()
        if not sun_tzu_db:
            return ""

        principles = sun_tzu_db.get("strategic_principles", {})
        key = "intelligence"  # Default strategy

        # --- LOGIC FOR SELECTING SUN TZU PRINCIPLE ---
        
        # 1. Low battery or long mission -> Energy Management
        if mission_brief.battery_percent < 40 or mission_brief.time_limit > 90:
            key = "energy_management"
            
        # 2. EW, Jamming, or specific threats -> Deception
        elif any(threat in ['РЕБ', 'Jamming', 'Decoy', 'Radar'] for threat in mission_brief.known_threats):
            key = "deception"
            
        # 3. Deep strike -> Speed and Stealth
        elif mission_brief.objective == 'deep_penetration_strike':
            key = "speed_and_stealth"
            
        # 4. Bad weather -> Surprise Attack (Enemy unprepared)
        elif mission_brief.weather_condition in ['stormy', 'rain', 'fog']:
            key = "surprise_attack"
            
        # 5. Critical mission with few resources -> Desperate Ground
        elif mission_brief.available_drones < 3 and 'critical' in mission_brief.constraints:
            key = "desperate_ground"
            
        return f"""
📜 SUN TZU DOCTRINE:
"{principles.get(key, {}).get('quote', '')}"
👉 APPLICATION: {principles.get(key, {}).get('application', '')}
"""

    def perform_deep_strategic_analysis(self, mission_history: List[MissionBrief]) -> str:
        """
        Performs a deep theoretical analysis of mission history using the BIOS persona.
        This does NOT generate immediate actions but refines the strategic worldview.
        """
        if not self.prompt_builder:
            return "PromptBuilder not available."

        # Summarize history
        context = f"Analyzed {len(mission_history)} past missions.\n"
        for m in mission_history[-5:]: # Last 5
            context += f"- Objective: {m.objective}, Result: {m.constraints.get('outcome', 'unknown')}\n"

        query = "Identify systemic contradictions in our current operation doctrine. Where is the 'blind spot'?"

        prompt = self.prompt_builder.build_theoretical_prompt(
            topic="Changes in Drone Warfare Doctrine",
            context=context,
            query=query
        )

        if self.use_mock:
            return "MOCK ANALYSIS: The system relies too heavily on GPS. The blind spot is electronic warfare resiliency."
        
        return self.llm.query(prompt)
    # REFLEX EVOLUTION - NEW TACTIC GENERATION
    # -----------------------------------------------------------
    
    def generate_new_reflex(self, experience_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate new tactical reflex from experience analysis.
        
        PROCESS:
        1. Analyze failed missions (negative rewards)
        2. Analyze successful missions (positive rewards)
        3. Apply Sun Tzu / Liddell Hart / 36 Stratagems
        4. Generate JSON reflex definition
        5. Validate structure
        
        Called during charging when LLM has time to think.
        
        Args:
            experience_data: {
                'failures': List of failed experiences (reward < 0),
                'successes': List of successful experiences (reward > 0),
                'current_reflexes': List of active reflex names
            }
            
        Returns:
            dict: JSON reflex definition or None if generation failed
            
        Example output:
        {
          "name": "ALTITUDE_ESCAPE",
          "description": "Climb rapidly when shot at low altitude",
          "trigger": {
            "conditions": [
              {"sensor": "audio.threat_detected", "operator": "==", "value": "GUNSHOT"},
              {"sensor": "altitude", "operator": "<", "value": 50}
            ],
            "logic": "AND"
          },
          "action_strategy": {
            "type": "AI_OPTIMIZED",
            "guidance": "Vertical escape from low-altitude threat",
            "constraints": {
              "throttle": [0.9, 1.0],
              "pitch": [-0.1, 0.1]
            }
          },
          "priority": 115,
          "cooldown": 5.0,
          "source": "LLM_ANALYSIS_2024_12_11",
          "risk_level": "HIGH"
        }
        """
        try:
            failures = experience_data.get('failures', [])
            successes = experience_data.get('successes', [])
            current_reflexes = experience_data.get('current_reflexes', [])
            
            if not failures:
                self.logger.info("No failures to analyze")
                return None
            
            # Load strategic knowledge
            sun_tzu_db = self._load_sun_tzu_strategies()
            stratagems = self._load_stratagems()
            liddell_hart = self._load_liddell_hart()
            
            # Build analysis prompt
            prompt = self._build_reflex_analysis_prompt(
                failures,
                successes,
                current_reflexes,
                sun_tzu_db,
                stratagems
            )
            
            # Query LLM
            if self.use_mock:
                response = self._mock_reflex_generation(failures)
            else:
                response = self.llm.query(prompt)
            
            # Parse JSON response
            reflex_def = self._parse_reflex_response(response)
            
            if reflex_def:
                self.logger.info(f"✅ Generated new reflex: {reflex_def['name']}")
                return reflex_def
            else:
                self.logger.warning("Failed to parse LLM response")
                return None
                
        except Exception:
            logging.exception("CRASH in generate_new_reflex")
            return None
    
    def _build_reflex_analysis_prompt(
        self,
        failures: List[Dict],
        successes: List[Dict],
        current_reflexes: List[str],
        sun_tzu_db: Dict,
        stratagems: List[Dict]
    ) -> str:
        """
        Build LLM prompt for reflex generation.
        
        STRUCTURE:
        1. Context: Current reflexes and their performance
        2. Failures: What went wrong
        3. Successes: What worked well
        4. Strategic guidance: Sun Tzu + 36 Stratagems
        5. Output format: JSON schema
        """
        try:
            # Analyze failure patterns
            failure_summary = self._summarize_failures(failures)
            success_summary = self._summarize_successes(successes)
            
            # Select relevant stratagem
            stratagem = stratagems[0] if stratagems else {}
            
            prompt = f"""
You are a tactical AI analyzing drone combat experience to generate new reflexes.

CURRENT REFLEXES:
{', '.join(current_reflexes)}

RECENT FAILURES (reward < 0):
{failure_summary}

RECENT SUCCESSES (reward > 0):
{success_summary}

STRATEGIC GUIDANCE (Sun Tzu - The Art of War):
{sun_tzu_db.get('core_principles', {}).get('adaptability', 'Adapt to changing conditions')}

36 STRATAGEMS (Current recommendation):
{stratagem.get('name', 'Unknown')}: {stratagem.get('description', '')}

TASK:
Analyze why the failures occurred and generate ONE new tactical reflex to address the pattern.

OUTPUT FORMAT (JSON only, no markdown):
{{
  "name": "TACTICAL_NAME",
  "description": "Brief explanation",
  "trigger": {{
    "conditions": [
      {{"sensor": "sensor.path", "operator": "==", "value": "VALUE"}}
    ],
    "logic": "AND"
  }},
  "action_strategy": {{
    "type": "AI_OPTIMIZED",
    "guidance": "Strategic explanation",
    "constraints": {{
      "throttle": [min, max],
      "pitch": [min, max],
      "roll": [min, max],
      "yaw": [min, max]
    }}
  }},
  "priority": 100,
  "cooldown": 5.0,
  "risk_level": "MEDIUM"
}}

AVAILABLE SENSORS:
- audio.threat_detected (values: "GUNSHOT", "ROTOR_BLADE", "EXPLOSION")
- audio.azimuth (0-360 degrees)
- altitude (meters)
- battery.level (0-100)
- rear_guard.threat_above (boolean)
- ghost_link.device_count (number of EW signals)
- mag_scan.powerline_detected (boolean)
- gps.spoofing_detected (boolean)
- vision (list of detected objects)

OPERATORS: ==, !=, >, <, >=, <=, in, not_in

CONSTRAINTS:
- throttle: 0.0-1.0 (0=cut, 0.5=hover, 1.0=max)
- pitch/roll/yaw: -1.0 to +1.0

Generate the new reflex:
"""
            return prompt
            
        except Exception:
            logging.exception("CRASH in _build_reflex_analysis_prompt")
            return ""
    
    def _summarize_failures(self, failures: List[Dict]) -> str:
        """
        Summarize failure patterns for LLM analysis.
        
        EXTRACTS:
        - Common trigger conditions
        - Actions taken (what reflex fired)
        - Outcomes (why it failed)
        - Environment (altitude, battery, threats)
        """
        try:
            if not failures:
                return "No failures recorded."
            
            summary_lines = []
            
            # Take last 10 failures
            recent_failures = failures[-10:]
            
            for i, exp in enumerate(recent_failures, 1):
                state = exp.get('state', {})
                action = exp.get('action', {})
                reward = exp.get('reward', 0.0)
                
                # Extract key info
                altitude = state.get('altitude', 0)
                battery = state.get('battery', {}).get('level', 100)
                threat = state.get('audio', {}).get('threat_detected', 'NONE')
                reflex = action.get('reflex_name', 'UNKNOWN')
                
                summary_lines.append(
                    f"{i}. Altitude={altitude:.0f}m, Battery={battery:.0f}%, "
                    f"Threat={threat}, Reflex={reflex}, Reward={reward:.1f}"
                )
            
            return "\n".join(summary_lines)
            
        except Exception:
            logging.exception("CRASH in _summarize_failures")
            return "Failed to summarize"
    
    def _summarize_successes(self, successes: List[Dict]) -> str:
        """
        Summarize successful actions for LLM to learn from.
        """
        try:
            if not successes:
                return "No successes recorded."
            
            summary_lines = []
            recent_successes = successes[-10:]
            
            for i, exp in enumerate(recent_successes, 1):
                state = exp.get('state', {})
                action = exp.get('action', {})
                reward = exp.get('reward', 0.0)
                
                altitude = state.get('altitude', 0)
                battery = state.get('battery', {}).get('level', 100)
                threat = state.get('audio', {}).get('threat_detected', 'NONE')
                reflex = action.get('reflex_name', 'UNKNOWN')
                
                summary_lines.append(
                    f"{i}. Altitude={altitude:.0f}m, Battery={battery:.0f}%, "
                    f"Threat={threat}, Reflex={reflex}, Reward={reward:.1f}"
                )
            
            return "\n".join(summary_lines)
            
        except Exception:
            logging.exception("CRASH in _summarize_successes")
            return "Failed to summarize"
    
    def _parse_reflex_response(self, llm_response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response into JSON reflex definition.
        
        HANDLES:
        - JSON inside markdown code blocks
        - Extra whitespace
        - Invalid JSON (returns None)
        """
        try:
            # Strip markdown code blocks
            response = llm_response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            response = response.strip()
            
            # Parse JSON
            reflex_def = json.loads(response)
            
            # Validate required fields
            required = ['name', 'trigger', 'action_strategy', 'priority']
            for field in required:
                if field not in reflex_def:
                    self.logger.error(f"Missing required field: {field}")
                    return None
            
            # Add metadata
            reflex_def['source'] = f"LLM_ANALYSIS_{datetime.now().strftime('%Y_%m_%d')}"
            reflex_def['cooldown'] = reflex_def.get('cooldown', 5.0)
            reflex_def['risk_level'] = reflex_def.get('risk_level', 'MEDIUM')
            
            return reflex_def
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON from LLM: {e}")
            self.logger.debug(f"Response was: {llm_response[:200]}")
            return None
        except Exception:
            logging.exception("CRASH in _parse_reflex_response")
            return None
    
    def _mock_reflex_generation(self, failures: List[Dict]) -> str:
        """
        Mock LLM response for testing without actual LLM.
        
        Generates a simple ALTITUDE_ESCAPE reflex based on failures.
        """
        try:
            # Analyze failures to determine pattern
            low_altitude_failures = sum(
                1 for exp in failures 
                if exp.get('state', {}).get('altitude', 100) < 50
            )
            
            if low_altitude_failures > len(failures) * 0.5:
                # Many low-altitude failures → Generate climb reflex
                return json.dumps({
                    "name": "ALTITUDE_ESCAPE",
                    "description": "Climb rapidly when shot at low altitude to exit kill zone",
                    "trigger": {
                        "conditions": [
                            {"sensor": "audio.threat_detected", "operator": "==", "value": "GUNSHOT"},
                            {"sensor": "altitude", "operator": "<", "value": 50}
                        ],
                        "logic": "AND"
                    },
                    "action_strategy": {
                        "type": "AI_OPTIMIZED",
                        "guidance": "Vertical escape from low-altitude sniper threat",
                        "constraints": {
                            "throttle": [0.9, 1.0],
                            "pitch": [-0.1, 0.1],
                            "roll": [-0.3, 0.3],
                            "yaw": [-0.3, 0.3]
                        }
                    },
                    "priority": 115,
                    "cooldown": 5.0,
                    "risk_level": "HIGH"
                })
            else:
                # Generic evasive maneuver
                return json.dumps({
                    "name": "RANDOM_EVASION",
                    "description": "Unpredictable evasive maneuver",
                    "trigger": {
                        "conditions": [
                            {"sensor": "audio.threat_detected", "operator": "!=", "value": "NONE"}
                        ],
                        "logic": "AND"
                    },
                    "action_strategy": {
                        "type": "AI_OPTIMIZED",
                        "guidance": "Random evasion to break enemy tracking",
                        "constraints": {
                            "throttle": [0.3, 0.8],
                            "pitch": [-0.5, 0.5],
                            "roll": [-0.8, 0.8],
                            "yaw": [-0.5, 0.5]
                        }
                    },
                    "priority": 90,
                    "cooldown": 3.0,
                    "risk_level": "MEDIUM"
                })
                
        except Exception:
            logging.exception("CRASH in _mock_reflex_generation")
            return "{}"

        strategy = principles.get(key, {})
        quote = strategy.get('quote', '')
        application = strategy.get('application', '')

        return f"""
📜 SUN TZU DOCTRINE:
"{quote}"
👉 APPLICATION: {application}
"""

    def _get_relevant_stratagem(self, mission_brief: MissionBrief) -> str:
        """Picks the best of the 36 Stratagems based on context."""
        stratagems = self._load_stratagems()
        if not stratagems:
            return ""

        candidates = []
        for s in stratagems:
            triggers = s.get("triggers", [])
            
            if "low_battery" in triggers and mission_brief.battery_percent < 30:
                candidates.append(s)
            if "decoy_available" in triggers and "PhantomDecoy" in self.available_modules:
                candidates.append(s)
            if "heavily_defended_target" in triggers and ("ППО" in mission_brief.known_threats or "Air Defense" in mission_brief.known_threats):
                candidates.append(s)
            if "electronic_warfare" in triggers and ("РЕБ" in mission_brief.known_threats or "Jamming" in mission_brief.known_threats):
                candidates.append(s)

        # Fallback to the first one if no specific trigger
        selected = candidates[0] if candidates else stratagems[0] 
        
        return f"""
⚔️ TACTICAL STRATAGEM #{selected['id']} ({selected['name']}):
📜 CONCEPT: {selected['original_concept']}
🤖 DRONE EXECUTION: {selected['drone_application']}
"""

    def _get_corporate_wisdom(self, mission_brief: MissionBrief) -> str:
        """Different business stratagems for specific resource/crisis contexts."""
        doctrine = self._load_corporate_doctrine()
        if not doctrine:
            return ""
            
        groups = doctrine.get('stratagem_groups', {})
        selected_item = None
        group_name = ""

        # Logic to pick a Corporate Stratagem
        
        # 1. Resource scarcity / Low Drones -> "Empty Fort" (Psychological)
        if mission_brief.available_drones < 5:
            group = groups.get('psychological_pressure', {})
            items = group.get('items', [])
            # Search for Empty Fort by name or id
            for item in items:
                if item['id'] == 32:
                    selected_item = item
                    group_name = group.get('name', '')
                    break
        
        # 2. Reconnaissance / Spying -> "Hide a Knife Behind a Smile"
        elif mission_brief.objective == 'reconnaissance':
            group = groups.get('psychological_pressure', {})
            items = group.get('items', [])
            for item in items:
                if item['id'] == 10:
                    selected_item = item
                    group_name = group.get('name', '')
                    break

        # 3. EW / Jamming -> "Kill with a Borrowed Knife"
        elif any(t in ['РЕБ', 'Jamming'] for t in mission_brief.known_threats):
           group = groups.get('deception_and_disorientation', {})
           items = group.get('items', [])
           for item in items:
               if item['id'] == 3:
                   selected_item = item
                   group_name = group.get('name', '')
                   break
        
        # Default -> "Indirect Action" Concept if nothing specific matched
        if not selected_item:
           phil = doctrine.get('philosophical_foundations', {}).get('indirect_strategy', {})
           return f"""
💼 CORPORATE WARFARE DOCTRINE (ASYMMETRIC):
💡 CONCEPT: {phil.get('concept', 'Indirect Action')}
📖 DESC: {phil.get('description', '')}
"""

        return f"""
💼 CORPORATE WARFARE STRATAGEM ({group_name}):
💡 STRATEGY: "{selected_item['name']}"
📖 INTERPRETATION: {selected_item['interpretation']}
🤖 APPLICATION: {selected_item['example_application']}
"""

    def _select_grand_strategy(self, mission_brief: MissionBrief) -> str:
        """
        Selects the GRAND STRATEGY between Sun Tzu, Clausewitz, and Liddell Hart.
        """
        liddell = self._load_liddell_hart()
        
        # 1. Fortified/Static Enemy -> LIDDELL HART (Maneuver & Dislocation)
        if "fortified" in mission_brief.known_threats or "high_density" in mission_brief.constraints:
            principle = liddell.get("indirect_approach_doctrine", {}).get("dislocation", {})
            return f"""
🌟 GRAND STRATEGY: LIDDELL HART (INDIRECT APPROACH)
"Direct attacks against a consolidated enemy are suicide."
DOCTRINE: {principle.get('quote', '')}
EXECUTION: {principle.get('application', '')}
"""

        # 2. Chaotic situation, EW, need for guile -> SUN TZU (Deception)
        elif "РЕБ" in mission_brief.known_threats or mission_brief.weather_condition != 'clear':
             return f"""
🌟 GRAND STRATEGY: SUN TZU (THE ART OF WAR)
{self._get_tactical_wisdom(mission_brief)}
"""

        # 3. Decisive strike required -> CLAUSEWITZ (Center of Gravity)
        elif mission_brief.objective == 'destroy_base':
             return """
🌟 GRAND STRATEGY: CLAUSEWITZ (SCHWERPUNKT)
"Identify the Center of Gravity. Focus all energy on this single point. Ignore peripherals."
"""
             
        # Default -> Liddell Hart (The Dilemma - best for swarms)
        else:
            principle = liddell.get("indirect_approach_doctrine", {}).get("alternative_objectives", {})
            return f"""
🌟 GRAND STRATEGY: LIDDELL HART (THE DILEMMA)
DOCTRINE: {principle.get('quote', '')}
EXECUTION: {principle.get('application', '')}
"""

    # -----------------------------------------------------------
    # PROMPT CONSTRUCTION & GENERATION
    # -----------------------------------------------------------

    def _build_military_prompt(self, mission_brief: MissionBrief, risk_report: dict = None) -> str:
        """
        Creates a structured prompt for the LLM combining all strategies.
        """
        # 1. Select Grand Strategy (The "Why" and "How")
        grand_strategy = self._select_grand_strategy(mission_brief)
        
        # 2. Select specific Stratagem (The "Trick")
        tactical_trick = self._get_relevant_stratagem(mission_brief)

        # 3. Select Corporate Wisdom (Modern Context)
        corp_wisdom = self._get_corporate_wisdom(mission_brief)
        
        # 4. Weather Risk Injection
        weather_context = f"Weather: {mission_brief.weather_condition}, Wind {mission_brief.wind_speed} km/h"
        if risk_report and self.prompt_builder:
             # Use PromptBuilder's probabilistic context generator
             weather_data = {'wind_speed': mission_brief.wind_speed}
             weather_context = self.prompt_builder._build_weather_context(weather_data, risk_report)

        base = f"""You are an advanced military AI tactical advisor integrated into the SmartBees drone swarm.
You combine ancient Eastern wisdom (Sun Tzu, 36 Stratagems), modern Western doctrine (Liddell Hart, Clausewitz), and Asymmetric Corporate Warfare strategies.

MISSION BRIEF:
Objective: {mission_brief.objective}
Target: {mission_brief.target_coords}
Available Drones: {mission_brief.available_drones}
Battery: {mission_brief.battery_percent}%
Time Limit: {mission_brief.time_limit} minutes
{weather_context}
Known Threats: {', '.join(mission_brief.known_threats)}

{grand_strategy}

{tactical_trick}

{corp_wisdom}

AVAILABLE CAPABILITIES:
{', '.join(self.available_modules)}

TASK:
Generate 5 operational scenarios for this mission.
You MUST apply the principles from the GRAND STRATEGY and the TACTICAL STRATAGEM in your execution steps.

CONSTRAINTS:
- No civilian casualties.
- Maintain battery reserve for return (20%).
- Avoid unnecessary risks.
- Prioritize mission success over speed.

OUTPUT FORMAT (strict JSON):
{{
  "scenarios": [
    {{
      "id": 1,
      "name": "Scenario Name (e.g. Operation Silent Wind)",
      "concept": "Brief tactical concept citing the strategy used",
      "modules_used": ["Module1", "Module2"],
      "execution_steps": [
        "Step 1: ...",
        "Step 2: ..."
      ],
      "success_probability": 0.85,
      "risk_level": "MEDIUM",
      "casualties_estimated": "10-15%",
      "advantages": ["Advantage 1"],
      "vulnerabilities": ["Weakness 1"],
      "distance_km": 100.0,
      "drones_required": 50,
      "time_limit_minutes": 120
    }}
  ]
}}
"""
        
        if not self.use_mock:
            # Add real-time context if LLM is active
            context_str = self.context.get_context()
            base += f"\n\nREAL-TIME CONTEXT:\n{context_str}"
        
        return base

    async def generate_scenarios(
        self, 
        mission_brief: MissionBrief
    ) -> List[TacticalScenario]:
        """
        Generates tactical scenarios based on the assignment.
        
        Args:
            mission_brief: Mission description from operator.
            
        Returns:
            List of valid tactical scenarios (top 5).
        """
        self.logger.info(f"🎯 Generating scenarios for: {mission_brief.objective}")
        
        # STEP 1: Context Collection
        # STEP 1: Context Collection
        self._build_context(mission_brief)
        
        # STEP 1.5: Weather Risk Analysis
        risk_report = {}
        if self.weather_service and mission_brief.target_coords:
             try:
                 lat, lon = mission_brief.target_coords
                 # Assuming target_coords is (lat, lon)
                 risk_report = self.weather_service.get_risk_analysis(lat, lon, mission_brief.time_limit)
                 self.logger.info(f"Probabilistic Risk Report: {risk_report.get('risk_score', 0)*100:.1f}% risk")
             except Exception as e:
                 self.logger.error(f"Weather risk analysis failed: {e}")

        # STEP 2: LLM Scenario Generation
        if self.use_mock:
            scenarios = self._generate_mock_scenarios(mission_brief)
        else:
            scenarios = await self._generate_llm_scenarios(mission_brief, risk_report)
        
        self.logger.info(f"📝 LLM generated {len(scenarios)} scenarios")
        
        # STEP 3: Physics Validation
        validated_scenarios = []
        for scenario in scenarios:
            feasible, reason = self._validate_physics(scenario, mission_brief)
            scenario.physically_feasible = feasible
            scenario.validation_notes = reason
            
            if feasible:
                # STEP 4: AI Risk Assessment
                if self.learner:
                    scenario.ai_risk_score = self._assess_risk_with_ai(scenario)
                validated_scenarios.append(scenario)
                self.logger.info(f"✅ {scenario.name}: feasible (risk={scenario.ai_risk_score:.2f})")
            else:
                self.logger.warning(f"❌ {scenario.name}: {reason}")
        
        # STEP 5: Ranking (success × (1-risk))
        validated_scenarios.sort(
            key=lambda s: s.success_probability * (1 - s.ai_risk_score),
            reverse=True
        )
        
        self.logger.info(f"🏆 Top scenarios ready: {len(validated_scenarios)}")
        return validated_scenarios[:5]  # Top 5

    def _build_context(self, mission_brief: MissionBrief):
        """
        Aggregates context for LLM from all available sources.
        """
        if self.use_mock:
            return
        
        # Current swarm state
        swarm_state = {
            'available_drones': mission_brief.available_drones,
            'avg_battery': mission_brief.battery_percent,
            'operational': True
        }
        
        # If Analytics is available - get real data
        if self.analytics:
            try:
                swarm_state = self.analytics.get_swarm_status()
            except:
                pass
        
        self.context.add_system_state(
            swarm_state,
            priority=ContextPriority.HIGH
        )
        
        # Available modules
        self.context.add_system_state({
            'modules_available': self.available_modules,
            'capabilities': {
                'max_range_km': 100,
                'max_altitude_m': 5000,
                'max_loiter_hours': 48  # With LineCharge
            }
        }, priority=ContextPriority.MEDIUM)
        
        # Intelligence data (threats)
        intel = {
            'known_threats': mission_brief.known_threats,
            'defenses': ['EW', 'Air Defense', 'Radars'],
            'terrain': 'mixed',
            'population_density': 'low'
        }
        self.context.add_environmental_data(
            intel,
            priority=ContextPriority.CRITICAL
        )
        
        # Mission as a critical event
        self.context.add_mission_update({
            'objective': mission_brief.objective,
            'target': mission_brief.target_coords,
            'deadline': mission_brief.time_limit,
            'constraints': mission_brief.constraints
        }, priority=ContextPriority.CRITICAL)

    async def _generate_llm_scenarios(
        self, 
        mission_brief: MissionBrief,
        risk_report: dict = None
    ) -> List[TacticalScenario]:
        """
        Generates scenarios via LLM inference.
        """
        prompt = self._build_military_prompt(mission_brief, risk_report)
        
        try:
            # Async request to LLM
            response = await self.llm.query_async(
                prompt,
                on_partial=lambda text: self.logger.debug(f"[LLM] {text[:50]}...")
            )
            
            # Parsing JSON response
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                 # Sometimes LLM adds markdown ```json ... ``` wrapper
                cleaned = response.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned)

            scenarios = []
            for raw in data.get('scenarios', []):
                scenario = TacticalScenario(
                    id=raw['id'],
                    name=raw['name'],
                    concept=raw['concept'],
                    modules_used=raw['modules_used'],
                    execution_steps=raw['execution_steps'],
                    success_probability=raw['success_probability'],
                    risk_level=raw['risk_level'],
                    casualties_estimated=raw.get('casualties_estimated', '0%'),
                    advantages=raw.get('advantages', []),
                    vulnerabilities=raw.get('vulnerabilities', []),
                    distance_km=raw.get('distance_km', 100.0),
                    drones_required=raw.get('drones_required', mission_brief.available_drones),
                    time_limit_minutes=raw.get('time_limit_minutes', mission_brief.time_limit)
                )
                scenarios.append(scenario)
            
            return scenarios
            
        except Exception as e:
            self.logger.error(f"LLM inference failed: {e}")
            return self._generate_mock_scenarios(mission_brief)

    def _generate_mock_scenarios(
        self, 
        mission_brief: MissionBrief
    ) -> List[TacticalScenario]:
        """
        Generates mock scenarios for testing (when LLM is unavailable).
        """
        self.logger.info("🔧 Using mock scenario generator")
        
        return [
            TacticalScenario(
                id=1,
                name="Energy Vampire (LineCharge Loitering)",
                concept="Long-duration loitering using enemy power infrastructure (Sun Tzu Logistics)",
                modules_used=['LineCharge', 'SwarmLink', 'BlockchainHiveMind'],
                execution_steps=[
                    "Phase 1: Infiltrate 100km deep at night using terrain masking",
                    "Phase 2: Land on high-voltage power lines near target area",
                    "Phase 3: Enter hibernation mode (Vampire Protocol)",
                    "Phase 4: Maintain mesh network for coordination",
                    "Phase 5: Activate on signal after 7 days",
                    "Phase 6: Simultaneous strike on convoy below"
                ],
                success_probability=0.82,
                risk_level="MEDIUM",
                casualties_estimated="5-10%",
                advantages=["Unlimited loitering", "Uses enemy infrastructure"],
                vulnerabilities=["Wire detection", "Ice/Wind"],
                distance_km=100.0,
                drones_required=50,
                time_limit_minutes=10080
            ),
            TacticalScenario(
                id=2,
                name="Phantom Swarm (Decoy Coordination)",
                concept="Create phantom radar signatures (Stratagem #6: Clamor in the East)",
                modules_used=['PhantomDecoy', 'TrojanTransport', 'SwarmManager'],
                execution_steps=[
                    "Phase 1: 10 real drones + 40 phantom signatures",
                    "Phase 2: Emit false radar cross-sections at Sector East",
                    "Phase 3: Force enemy to engage phantoms",
                    "Phase 4: Real drones exploit gaps in coverage from West",
                    "Phase 5: Strike during ammunition reload"
                ],
                success_probability=0.90,
                risk_level="LOW",
                casualties_estimated="5%",
                advantages=["Overwhelms tracking", "Low exposure"],
                vulnerabilities=["Sophisticated radars"],
                distance_km=70.0,
                drones_required=10,
                time_limit_minutes=45
            )
        ]

    def _validate_physics(
        self, 
        scenario: TacticalScenario,
        mission_brief: MissionBrief
    ) -> Tuple[bool, str]:
        """
        Checks physical feasibility of the scenario.
        Returns: (feasible: bool, reason: str)
        """
        # Energy calculation
        distance_m = scenario.distance_km * 1000
        
        # Assumption: 150W consumption, 15 m/s speed
        power_consumption = 150  # Watts
        speed = 15.0  # m/s
        
        time_required_sec = distance_m / speed
        energy_required_wh = (power_consumption * time_required_sec) / 3600
        
        # Battery: 3S LiPo (12.6V nominal), 8.5Ah
        battery_capacity_wh = 12.6 * 8.5  # ~107 Wh
        energy_available_wh = battery_capacity_wh * (mission_brief.battery_percent / 100.0)
        
        # 20% reserve for return
        energy_usable_wh = energy_available_wh * 0.8
        
        if energy_required_wh > energy_usable_wh:
            return False, f"Insufficient battery: need {energy_required_wh:.1f}Wh, have {energy_usable_wh:.1f}Wh"
        
        # Time check
        time_required_min = time_required_sec / 60
        if time_required_min > scenario.time_limit_minutes:
            return False, f"Time limit exceeded: {time_required_min:.1f}min > {scenario.time_limit_minutes}min"
        
        # Drone count check
        if scenario.drones_required > mission_brief.available_drones:
            return False, f"Not enough drones: need {scenario.drones_required}, have {mission_brief.available_drones}"
        
        return True, "Physics validated ✓"

    def _assess_risk_with_ai(self, scenario: TacticalScenario) -> float:
        """
        AI risk assessment via trained RL model.
        Returns: Risk score (0.0 = no risk, 1.0 = certain failure)
        """
        if not self.learner:
            # Fallback: basic assessment based on risk_level string
            risk_map = {'LOW': 0.1, 'MEDIUM': 0.3, 'HIGH': 0.6, 'CRITICAL': 0.9}
            return risk_map.get(scenario.risk_level, 0.5)
        
        # Create scenario state vector for the Neural Network
        state = {
            'gps': {'alt': 100.0, 'speed': 15.0},
            'ahrs': {'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0},
            'barometer': {'raw_baro': 1013.25, 'vsi': 0.0},
            'battery': {'voltage': 12.0, 'current': 8.0},
            'vision': {'brightness': 0.7},
            'weather_api': {'temp_c': 20.0},
            # Additional scenario metrics
            '_distance_km': scenario.distance_km,
            '_drones_count': scenario.drones_required,
            '_threats': len(scenario.vulnerabilities)
        }
        
        try:
            # Use trained policy for assessment
            state_vec = self.learner.buffer._serialize_state(state)
            action_vec = self.learner.policy.predict(state_vec)
            
            # Convert action magnitude to risk score
            # Logic: larger corrective actions imply higher instability/risk
            risk_score = float(abs(action_vec).mean())
            risk_score = min(1.0, max(0.0, risk_score))
            
            return risk_score
            
        except Exception as e:
            self.logger.error(f"AI risk assessment failed: {e}")
            return 0.5

    def print_scenario_summary(self, scenarios: List[TacticalScenario]):
        """
        Prints a formatted summary of generated scenarios.
        """
        print("\n" + "="*80)
        print("🎯 TACTICAL SCENARIOS GENERATED")
        print("="*80)
        
        for i, s in enumerate(scenarios, 1):
            score = s.success_probability * (1 - s.ai_risk_score)
            
            print(f"\n{i}. {s.name}")
            print(f"   {'─'*70}")
            print(f"   Concept: {s.concept}")
            print(f"   Success Probability: {s.success_probability*100:.1f}%")
            print(f"   AI Risk Score: {s.ai_risk_score*100:.1f}%")
            print(f"   Combined Score: {score*100:.1f}%")
            print(f"   Risk Level: {s.risk_level}")
            print(f"   Casualties: {s.casualties_estimated}")
            print(f"   Distance: {s.distance_km} km")
            print(f"   Drones: {s.drones_required}")
            print(f"   Time: {s.time_limit_minutes} min")
            print(f"   \n   Modules: {', '.join(s.modules_used)}")
            
            if s.advantages:
                print(f"   ✓ Advantages:")
                for adv in s.advantages:
                    print(f"     • {adv}")
            
            if s.vulnerabilities:
                print(f"   ⚠ Vulnerabilities:")
                for vuln in s.vulnerabilities:
                    print(f"     • {vuln}")
            
            print(f"   \n   Execution:")
            for step in s.execution_steps:
                print(f"     → {step}")
            
            if not s.physically_feasible:
                print(f"   \n   ❌ VALIDATION: {s.validation_notes}")
        
        print("\n" + "="*80 + "\n")


# -----------------------------------------------------------
# MAIN ENTRY POINT FOR TESTING
# -----------------------------------------------------------

async def main():
    """
    Demo of scenario generator operation.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Creating generator (using mock for demo if LLM not present)
    generator = MissionGenerator(use_mock_llm=True)
    
    # Mission description
    mission = MissionBrief(
        objective='destroy_enemy_command_post',
        target_coords=(48.123, 39.456),
        available_drones=50,
        battery_percent=75.0,
        time_limit=120,  # 2 hours
        weather_condition='cloudy',
        wind_speed=15.0,
        known_threats=['РЕБ', 'ППО Панцир', 'Радари'],
        constraints={
            'no_fly_zones': [],
            'min_altitude': 50,
            'max_altitude': 500
        }
    )
    
    # Generating scenarios
    scenarios = await generator.generate_scenarios(mission)
    
    # Outputting results
    generator.print_scenario_summary(scenarios)
    
    # Saving to file
    output = {
        'mission': {
            'objective': mission.objective,
            'target': mission.target_coords,
            'generated_at': datetime.now().isoformat()
        },
        'scenarios': [
            {
                'id': s.id,
                'name': s.name,
                'score': s.success_probability * (1 - s.ai_risk_score),
                'feasible': s.physically_feasible
            }
            for s in scenarios
        ]
    }
    
    with open('tactical_scenarios.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("💾 Results saved to tactical_scenarios.json")


if __name__ == '__main__':
    asyncio.run(main())