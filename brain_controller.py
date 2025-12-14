# smartbees/ai/brain_controller.py
import gc
import time
import logging
from typing import Optional

class BrainSensorController:
    """
    Виконавчий механізм керування сенсорами та AI.
    Не приймає рішень сам — виконує накази 'Мозку' (AnalyticCore).
    """
    def __init__(self, audio_sensor, llm_engine=None, sync_service=None, flight_recorder=None):
        self.audio = audio_sensor
        self.llm = llm_engine
        self.sync = sync_service
        self.recorder = flight_recorder
        self.logger = logging.getLogger("BrainController")
        
        # Стан системи
        self.is_dreaming = False
        self.last_mic_activation = 0
        
        # Динамічні параметри (встановлюються Мозком)
        self.mic_interval = 0.0  # 0 = завжди увімкнено
        self.mic_duration = 0.0
        self.mic_threshold_db = -30.0
        
        self.logger.info("🧠 Brain Sensor Controller Initialized")

    def apply_flight_strategy(self, altitude: float, speed: float, threat_level: float):
        """
        РЕЖИМ ПОЛЬОТУ: 'Мозок' активно керує параметрами на основі телеметрії.
        LLM = СПИТЬ (економія).
        """
        if self.is_dreaming:
            self._wake_up_from_dream()

        # --- ЛОГІКА МОЗКУ (Динамічне керування вухами) ---
        
        # 1. Якщо ми низько (шпигуємо) або висимо на місці -> Слухати часто
        if altitude < 15.0 or speed < 1.0:
            self.mic_interval = 10.0  # Кожні 10 сек
            self.mic_duration = 5.0
            self.mic_threshold_db = -40.0  # висока чутливість
            
        # 2. Якщо ми високо або швидко летимо -> Слухати рідко (шум вітру заважає)
        elif altitude > 50.0 or speed > 10.0:
            self.mic_interval = 60.0  # Раз на хвилину
            self.mic_duration = 3.0
            self.mic_threshold_db = -10.0  # тільки дуже гучні звуки
            
        # 3. Якщо рівень загрози високий -> Слухати ПОСТІЙНО
        if threat_level > 0.8:
            self.mic_interval = 0.0   # Постійний моніторинг
            self.mic_threshold_db = -40.0
        
        # Виконання циклу мікрофона
        self._manage_mic_cycle()

    def enter_charging_mode(self):
        """
        РЕЖИМ ЗАРЯДКИ: 'Мозок' дрімає, LLM прокидається.
        Запуск процесів навчання та аналізу.
        """
        if not self.is_dreaming:
            self.logger.info("🔌 CHARGING CONNECTED. Entering DREAM STATE...")
            self.is_dreaming = True
            
            # 1. Фізичний відпочинок сенсорів (Рекалібрування)
            self._recalibrate_sensors()
            
            # 2. Очищення пам'яті ("Детокс мозку")
            self._cleanup_system_resources()
            
            # 3. Мікрофон на повну (охорона периметра поки спимо)
            self.audio.resume()
            
            # 4. Запуск "Сновидінь" (Аналіз та Навчання)
            self._process_dreams()

    def _manage_mic_cycle(self):
        """Вмикає/вимикає мікрофон згідно з поточними параметрами."""
        if self.mic_interval == 0.0:
            # Постійний режим
            if self.audio.is_paused:
                self.audio.resume()
            return

        current_time = time.time()
        time_since = current_time - self.last_mic_activation
        
        # Логіка циклу
        if not self.audio.is_paused:
            # Зараз слухаємо. Чи час спати?
            if time_since > self.mic_duration:
                self.audio.pause()
        else:
            # Зараз спимо. Чи час прокидатися?
            if time_since > (self.mic_duration + self.mic_interval):
                self.audio.resume()
                self.last_mic_activation = current_time

    def _recalibrate_sensors(self):
        """Лікуємо 'блукаючі струми' та дрейф гіроскопів."""
        self.logger.info("🔧 MAINTENANCE: Zeroing sensor drift...")
        
        # Гіроскопам потрібен повний спокій для визначення "нуля"
        if hasattr(self.audio, 'calibrate_noise_floor'):
            # Заміряємо рівень тиші, щоб відсіяти шум власної плати
            self.audio.calibrate_noise_floor()
            
        # Тут би ми викликали калібрування IMU:
        # self.imu.calibrate_bias() 
        
        self.logger.info("✅ Sensors recalibrated.")

    def _cleanup_system_resources(self):
        """Боротьба з накопиченням помилок у пам'яті."""
        # Примусовий запуск Garbage Collector
        gc.collect() 
        
        # Очищення кешів LLM (вони теж "засмічуються" контекстом)
        if self.llm and hasattr(self.llm, 'reset_context_window'):
            self.llm.reset_context_window()  # Скидаємо "короткочасну пам'ять"
            
        self.logger.info("🧹 RAM Cleanup: Freed resources. System fresh.")

    def _process_dreams(self):
        """
        LLM аналізує день, робить висновки і обмінюється досвідом.
        Поки 'тіло' відпочиває і охолоджується, 
        'підсвідомість' повільно аналізує помилки минулого польоту.
        """
        self.logger.info("🧠 LLM Waking up... Analyzing Flight Logs...")
        
        if self.llm:
            # 1. Отримати дані польоту ("спогади")
            if self.recorder:
                logs = self.recorder.get_recent_logs()
                self.logger.debug(f"Retrieved {len(logs) if logs else 0} log entries")
            
            # 2. LLM думає ("рефлексія")
            # prompt = f"Analyze these incidents: {logs}. Suggest tactics update."
            # insights = self.llm.query(prompt)
            # self.logger.info(f"💡 LLM Insight: {insights}")
            
            # 3. Обмін вагами ("колективний розум")
            if self.sync:
                self.logger.info("📡 Uploading experience weights to Swarm Cloud...")
                self.sync.sync_weights()  # Обмін даними з сервером
            
        else:
            self.logger.warning("LLM not initialized, cannot dream.")

    def _wake_up_from_dream(self):
        """Вихід з режиму сновидінь при старті польоту."""
        self.is_dreaming = False
        self.logger.info("🚁 TAKEOFF DETECTED. Waking up 'AnalyticCore'. LLM going to sleep.")
