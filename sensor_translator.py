# smartbees/app/llm/sensor_translator.py
# TRANSLATOR: Raw Sensors -> Natural Language Context for LLM
# Reduces token usage by summarizing massive data into semantic tags.
# REASON: LLM needs human-readable SITREP, not raw sensor values

import logging
import numpy as np


class SensorTranslator:
    """
    Converts the 48-sensor data stream into a 'SITREP' (Situation Report) 
    that the LLM can analyze during the 'Dreaming/Charging' phase.
    
    DESIGN PHILOSOPHY:
    - Raw sensors = numbers (e.g., "RSSI: -85dBm")
    - LLM needs context (e.g., "Weak Signal - Possible Jamming")
    - Reduces token usage: 48 sensors → ~200 tokens of meaningful text
    """

    @staticmethod
    def generate_sitrep(sensor_data: dict) -> str:
        """
        Generates a concise textual summary of the drone's status.
        
        Args:
            sensor_data: Full sensor dict from SensorManager.get_all_data()
            
        Returns:
            str: Human-readable situation report
        """
        try:
            reports = []

            # ============================================================
            # 1. NAVIGATION INTEGRITY (GPS Anti-Spoofing)
            # ============================================================
            gnss = sensor_data.get('gnss_raw', {})
            gnss_measurements = gnss.get('measurements', [])
            
            if gnss_measurements:
                # Calculate spoofing indicators
                spoof_count = sum(
                    1 for sat in gnss_measurements 
                    if sat.get('cn0', 0) < 20 or sat.get('pseudorange_rate', 0) == 0
                )
                total_sats = len(gnss_measurements)
                
                if spoof_count > 3 and total_sats > 0:
                    spoof_ratio = (spoof_count / total_sats) * 100
                    reports.append(
                        f"⚠️ NAV: GPS SPOOFING DETECTED "
                        f"({spoof_count}/{total_sats} sats compromised = {spoof_ratio:.0f}%). "
                        f"Trust Level: LOW. Recommend VISUAL NAV."
                    )
                else:
                    reports.append("✅ NAV: GNSS Integrity Nominal.")
            else:
                reports.append("⚠️ NAV: NO GNSS DATA (Indoor or Jammed)")

            # ============================================================
            # 2. ELECTRONIC WARFARE (EW) - RF Spectrum Analysis
            # ============================================================
            # Check WiFi noise floor (jamming indicator)
            wifi_rtt = sensor_data.get('wifi_rtt', {})
            wifi_noise = wifi_rtt.get('noise_floor', -100)
            
            # Check cellular signal quality
            cell_nav = sensor_data.get('magnetic_anomaly', {})  # TODO: Replace with actual cell data key
            
            ew_threats = []
            
            # Strong WiFi noise = possible jamming
            if wifi_noise > -60:
                ew_threats.append("WiFi Jamming (Noise: {:.0f}dBm)".format(wifi_noise))
            
            # TODO: Add FM radio scanner data when available
            # fm_signals = sensor_data.get('fm_signals', [])
            # if any(s['strength'] > -40 for s in fm_signals):
            #     ew_threats.append("High-Power RF Interference")
            
            if ew_threats:
                reports.append(f"☢️ EW: ACTIVE JAMMING DETECTED - {', '.join(ew_threats)}")
            else:
                reports.append("✅ EW: RF Spectrum Clean")

            # ============================================================
            # 3. ACOUSTIC THREATS (Gunshots, Hostile Drones)
            # ============================================================
            acoustic = sensor_data.get('acoustic', {})
            
            if acoustic:
                gunshot_prob = acoustic.get('gunshot_prob', 0)
                drone_prob = acoustic.get('drone_prob', 0)
                azimuth = acoustic.get('azimuth', 0)
                
                if gunshot_prob > 0.8:
                    reports.append(
                        f"💥 COMBAT: GUNSHOTS detected from Azimuth {azimuth:.0f}°. "
                        f"Confidence: {gunshot_prob*100:.0f}%"
                    )
                elif drone_prob > 0.7:
                    reports.append(
                        f"🛸 COMBAT: HOSTILE DRONE signature detected. "
                        f"Azimuth {azimuth:.0f}°"
                    )

            # ============================================================
            # 4. PHYSICAL HEALTH (Vibration, Temperature, Tamper)
            # ============================================================
            vibro_health = sensor_data.get('vibration_health')
            
            if vibro_health and isinstance(vibro_health, (int, float)):
                if vibro_health < 50:
                    reports.append(
                        f"🔧 HEALTH: MECHANICAL FAILURE IMMINENT. "
                        f"Vibration Health: {vibro_health}%. "
                        f"Propeller imbalance or motor damage."
                    )
            
            # Tamper seal (Physical breach detection)
            imu_data = sensor_data.get('imu', {})
            mag_data = imu_data.get('mag') if imu_data else None
            
            # Simple tamper detection: Sudden magnetic field change
            # (Real implementation would use HallTamperSeal sensor)
            if mag_data:
                mag_magnitude = np.linalg.norm(mag_data) if isinstance(mag_data, (list, tuple)) else 0
                if mag_magnitude < 20 or mag_magnitude > 80:  # Earth field ~50μT
                    reports.append(
                        "🚨 SECURITY: MAGNETIC ANOMALY. "
                        "Possible case opening or hostile magnet."
                    )

            # ============================================================
            # 5. ENVIRONMENT (Visibility, Obstacles)
            # ============================================================
            environment = sensor_data.get('environment', {})
            
            if environment:
                humidity = environment.get('humidity', 0)
                light_level = environment.get('light_level', 0)
                
                if humidity > 95:
                    reports.append(
                        "☁️ ENV: ZERO VISIBILITY (Fog/Cloud). "
                        "Optical systems degraded. Use RADAR/LIDAR."
                    )
                
                if light_level < 10:
                    reports.append("🌙 ENV: LOW LIGHT. Night vision required.")

            # ============================================================
            # 6. POWER STATUS (Battery, Charging)
            # ============================================================
            battery = sensor_data.get('battery', {})
            if battery:
                level = battery.get('level', 100)
                charging = battery.get('charging', False)
                
                if charging:
                    reports.append(f"🔌 POWER: CHARGING on power line (Level: {level}%)")
                elif level < 20:
                    reports.append(f"🔋 POWER: CRITICAL BATTERY ({level}%). RTB Immediate.")
                elif level < 40:
                    reports.append(f"⚠️ POWER: LOW BATTERY ({level}%). Plan RTB.")

            # ============================================================
            # DEFAULT: All Systems Nominal
            # ============================================================
            if not reports:
                return "STATUS: ALL SYSTEMS NOMINAL. PATROL ROUTINE."
                
            return "\n".join(reports)
            
        except Exception:
            logging.exception("CRASH in SensorTranslator.generate_sitrep")
            return "ERROR: Sensor translation failed"

    @staticmethod
    def create_learning_prompt(flight_log: list) -> str:
        """
        Summarizes a whole flight for the LLM to learn from.
        Used during charging phase to create mission debrief.
        
        Args:
            flight_log: List of sensor_data snapshots throughout flight
            
        Returns:
            str: Mission summary prompt for LLM
        """
        try:
            if not flight_log:
                return "NO DATA: Flight log empty"
            
            # Get start and end states
            start_state = SensorTranslator.generate_sitrep(flight_log[0])
            end_state = SensorTranslator.generate_sitrep(flight_log[-1])
            
            # Count critical events
            gps_spoof_count = 0
            ew_incidents = 0
            combat_events = 0
            
            for snapshot in flight_log:
                sitrep = SensorTranslator.generate_sitrep(snapshot)
                if "SPOOFING" in sitrep:
                    gps_spoof_count += 1
                if "JAMMING" in sitrep:
                    ew_incidents += 1
                if "COMBAT" in sitrep or "GUNSHOT" in sitrep:
                    combat_events += 1
            
            # Calculate mission duration
            duration = len(flight_log) * 0.1  # Assuming 10Hz logging = 0.1s per frame
            
            return f"""
MISSION DEBRIEF - DURATION: {duration:.0f}s
==========================================

START STATUS:
{start_state}

END STATUS:
{end_state}

INCIDENTS:
- GPS Spoofing Events: {gps_spoof_count}
- EW Jamming Incidents: {ew_incidents}
- Combat Engagements: {combat_events}

ANALYSIS TASK:
1. Why did GPS reliability degrade? (Spoofing or terrain?)
2. Was EW response effective? (Did we switch to visual nav?)
3. Suggest tactical improvements for next mission.
4. Identify hardware failures or sensor degradation.

STRATEGIC RECOMMENDATION:
[LLM GENERATES THIS]
"""
        except Exception:
            logging.exception("CRASH in SensorTranslator.create_learning_prompt")
            return "ERROR: Learning prompt generation failed"

    @staticmethod
    def get_critical_alerts(sensor_data: dict) -> list:
        """
        Extracts only CRITICAL alerts that require immediate action.
        Used for real-time decision making during flight.
        
        Returns:
            list: ["ALERT_TYPE: message", ...]
        """
        try:
            sitrep = SensorTranslator.generate_sitrep(sensor_data)
            
            # Extract lines starting with critical symbols
            critical_lines = [
                line for line in sitrep.split('\n')
                if line.startswith(('⚠️', '☢️', '💥', '🚨', '🔋'))
            ]
            
            return critical_lines
            
        except Exception:
            logging.exception("CRASH in SensorTranslator.get_critical_alerts")
            return []
