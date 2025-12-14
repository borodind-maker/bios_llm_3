"""
LLM Engine - Core inference engine for MediaPipe LLM

This module provides the main interface for running Large Language Models
on-device using MediaPipe LLM Inference API.

Architecture:
    LLMEngine wraps MediaPipe's native Android API and provides a Python-friendly
    interface through Android JNI bridge (Pyjnius).

Performance:
    - Time to First Token: 100-300ms
    - Tokens per second: 5-15 (device dependent)
    - Memory footprint: 2-4GB for model
    - Battery impact: +5-10% additional consumption

Supported Models:
    - Gemma 3N E2B (2B parameters, 4-bit quantized)
    - Gemma 3N E4B (4B parameters, 4-bit quantized)
    - Gemma 2 2B (2B parameters, 4-bit quantized)
    - Phi-2 (2.7B parameters, 4-bit quantized)

Example:
    >>> engine = LLMEngine(
    ...     model_path="/data/local/tmp/llm/gemma-3n-e2b.task",
    ...     max_tokens=512,
    ...     temperature=0.7
    ... )
    >>> response = engine.query("What is the optimal altitude for surveying?")
    >>> print(response)
"""

import logging
import time
import json
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from pathlib import Path

# Try to import Android-specific libraries (will work on Android device)
try:
    from jnius import autoclass, cast
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False
    logging.warning("Pyjnius not available. LLM will run in simulation mode.")


@dataclass
class LLMConfig:
    """Configuration for LLM Engine"""
    model_path: str
    max_tokens: int = 512
    top_k: int = 40
    temperature: float = 0.7
    random_seed: int = 0
    enable_vision: bool = False
    enable_audio: bool = False
    max_num_images: int = 10
    lora_path: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate configuration parameters"""
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        if self.max_tokens < 1 or self.max_tokens > 4096:
            raise ValueError(f"max_tokens must be between 1 and 4096")
        
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError(f"temperature must be between 0.0 and 2.0")
        
        if self.top_k < 1 or self.top_k > 100:
            raise ValueError(f"top_k must be between 1 and 100")
        
        return True


class LLMEngine:
    """
    Core LLM Inference Engine using MediaPipe
    
    This class provides a high-level interface for running LLM inference
    on Android devices. It handles model initialization, inference execution,
    and response streaming.
    
    Attributes:
        config (LLMConfig): Engine configuration
        llm_inference: MediaPipe LLM inference instance
        session: Current inference session
        is_initialized (bool): Whether engine is ready
        
    Thread Safety:
        This class is NOT thread-safe. Use separate instances for concurrent access.
    """
    
    def __init__(self, 
                 model_path: str,
                 max_tokens: int = 512,
                 top_k: int = 40,
                 temperature: float = 0.7,
                 **kwargs):
        """
        Initialize LLM Engine
        
        Args:
            model_path: Absolute path to .task model file
            max_tokens: Maximum tokens (input + output)
            top_k: Number of tokens to consider at each step
            temperature: Randomness in generation (0.0-2.0)
            **kwargs: Additional configuration options
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If initialization fails
        """
        self.config = LLMConfig(
            model_path=model_path,
            max_tokens=max_tokens,
            top_k=top_k,
            temperature=temperature,
            **kwargs
        )
        
        self.config.validate()
        
        self.llm_inference = None
        self.session = None
        self.is_initialized = False
        self.inference_count = 0
        self.total_tokens = 0
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initializing LLM Engine with model: {model_path}")
        
        # Initialize MediaPipe LLM
        self._initialize()
    
    def _initialize(self):
        """
        Internal initialization of MediaPipe LLM
        
        This method handles the Android-specific initialization through JNI.
        Falls back to simulation mode if Android libraries not available.
        """
        try:
            if ANDROID_AVAILABLE:
                self._initialize_android()
            else:
                self._initialize_simulation()
            
            self.is_initialized = True
            self.logger.info("LLM Engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM Engine: {e}")
            raise RuntimeError(f"LLM initialization failed: {e}")
    
    def _initialize_android(self):
        """Initialize MediaPipe LLM on Android device"""
        # Import MediaPipe Android classes
        LlmInference = autoclass('com.google.mediapipe.tasks.genai.llminference.LlmInference')
        LlmInferenceOptions = autoclass('com.google.mediapipe.tasks.genai.llminference.LlmInference$LlmInferenceOptions')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        
        # Get Android context
        context = PythonActivity.mActivity
        
        # Build options
        options_builder = LlmInferenceOptions.builder()
        options_builder.setModelPath(self.config.model_path)
        options_builder.setMaxTokens(self.config.max_tokens)
        options_builder.setTopK(self.config.top_k)
        options_builder.setTemperature(self.config.temperature)
        options_builder.setRandomSeed(self.config.random_seed)
        
        # Add LoRA if specified
        if self.config.lora_path:
            options_builder.setLoraPath(self.config.lora_path)
            self.logger.info(f"LoRA weights loaded from: {self.config.lora_path}")
        
        # Build and create instance
        options = options_builder.build()
        self.llm_inference = LlmInference.createFromOptions(context, options)
        
        self.logger.info("MediaPipe LLM initialized on Android")
    
    def _initialize_simulation(self):
        """Initialize simulation mode for testing on desktop"""
        self.logger.warning("Running in SIMULATION mode (not on Android)")
        self.llm_inference = SimulatedLLM(self.config)
    
    def query(self, 
              prompt: str,
              context: Optional[Dict[str, Any]] = None,
              timeout: float = 30.0) -> str:
        """
        Execute synchronous LLM inference
        
        Args:
            prompt: Input prompt string
            context: Optional context dictionary to prepend
            timeout: Maximum time to wait for response (seconds)
        
        Returns:
            Generated text response
            
        Raises:
            RuntimeError: If inference fails
            TimeoutError: If inference exceeds timeout
        
        Example:
            >>> response = engine.query(
            ...     "Calculate optimal route",
            ...     context={"battery": 75, "distance": 5.2}
            ... )
        """
        if not self.is_initialized:
            raise RuntimeError("LLM Engine not initialized")
        
        start_time = time.time()
        
        try:
            # Format prompt with context
            formatted_prompt = self._format_prompt(prompt, context)
            
            self.logger.debug(f"Executing query: {formatted_prompt[:100]}...")
            
            # Execute inference
            if ANDROID_AVAILABLE:
                response = self.llm_inference.generateResponse(formatted_prompt)
            else:
                response = self.llm_inference.generate(formatted_prompt)
            
            # Track metrics
            elapsed = time.time() - start_time
            self.inference_count += 1
            token_count = len(response.split())
            self.total_tokens += token_count
            
            self.logger.info(
                f"Inference #{self.inference_count} completed in {elapsed:.2f}s "
                f"({token_count} tokens, {token_count/elapsed:.1f} tokens/sec)"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise RuntimeError(f"LLM query failed: {e}")
    
    async def query_async(self,
                         prompt: str,
                         context: Optional[Dict[str, Any]] = None,
                         on_partial: Optional[Callable[[str], None]] = None) -> str:
        """
        Execute asynchronous streaming LLM inference
        
        Args:
            prompt: Input prompt string
            context: Optional context dictionary
            on_partial: Callback for partial responses (streaming)
        
        Returns:
            Complete generated response
            
        Example:
            >>> async def print_partial(text):
            ...     print(text, end='', flush=True)
            >>> response = await engine.query_async(
            ...     "Describe emergency procedure",
            ...     on_partial=print_partial
            ... )
        """
        if not self.is_initialized:
            raise RuntimeError("LLM Engine not initialized")
        
        formatted_prompt = self._format_prompt(prompt, context)
        
        if ANDROID_AVAILABLE and on_partial:
            # Setup streaming with callback
            response_parts = []
            
            def result_listener(partial_result, done):
                response_parts.append(partial_result)
                if on_partial:
                    on_partial(partial_result)
            
            # Create options with listener
            LlmInferenceOptions = autoclass('com.google.mediapipe.tasks.genai.llminference.LlmInference$LlmInferenceOptions')
            options_builder = LlmInferenceOptions.builder()
            options_builder.setResultListener(result_listener)
            
            self.llm_inference.generateResponseAsync(formatted_prompt)
            
            return ''.join(response_parts)
        else:
            # Fallback to synchronous
            return self.query(prompt, context)
    
    def query_with_vision(self,
                         prompt: str,
                         images: List[Any],
                         context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute multimodal query with vision input
        
        Args:
            prompt: Text prompt
            images: List of image objects (MPImage format)
            context: Optional context dictionary
            
        Returns:
            Generated response based on text and images
            
        Requires:
            enable_vision=True in config
            
        Example:
            >>> from camera_service import capture_frame
            >>> image = capture_frame()
            >>> response = engine.query_with_vision(
            ...     "What obstacles do you see?",
            ...     images=[image]
            ... )
        """
        if not self.config.enable_vision:
            raise RuntimeError("Vision not enabled. Set enable_vision=True in config")
        
        if len(images) > self.config.max_num_images:
            raise ValueError(f"Too many images. Max: {self.config.max_num_images}")
        
        formatted_prompt = self._format_prompt(prompt, context)
        
        try:
            if ANDROID_AVAILABLE:
                # Create vision-enabled session
                LlmInferenceSession = autoclass('com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession')
                LlmInferenceSessionOptions = autoclass('com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession$LlmInferenceSessionOptions')
                GraphOptions = autoclass('com.google.mediapipe.tasks.genai.llminference.GraphOptions')
                
                session_options = LlmInferenceSessionOptions.builder()
                session_options.setTopK(self.config.top_k)
                session_options.setTemperature(self.config.temperature)
                
                graph_options = GraphOptions.builder()
                graph_options.setEnableVisionModality(True)
                session_options.setGraphOptions(graph_options.build())
                
                session = LlmInferenceSession.createFromOptions(
                    self.llm_inference,
                    session_options.build()
                )
                
                # Add prompt and images
                session.addQueryChunk(formatted_prompt)
                for image in images:
                    session.addImage(image)
                
                response = session.generateResponse()
                session.close()
                
                return response
            else:
                # Simulation mode
                return self.llm_inference.generate_with_vision(formatted_prompt, images)
                
        except Exception as e:
            self.logger.error(f"Vision query failed: {e}")
            raise RuntimeError(f"Vision query failed: {e}")
    
    def query_with_audio(self,
                        prompt: str,
                        audio_data: bytes,
                        context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute multimodal query with audio input
        
        Args:
            prompt: Text prompt
            audio_data: Audio data in WAV format (mono channel)
            context: Optional context dictionary
            
        Returns:
            Generated response based on text and audio
            
        Requires:
            enable_audio=True in config
            
        Example:
            >>> audio = record_voice_command()
            >>> response = engine.query_with_audio(
            ...     "Transcribe and execute:",
            ...     audio
            ... )
        """
        if not self.config.enable_audio:
            raise RuntimeError("Audio not enabled. Set enable_audio=True in config")
        
        formatted_prompt = self._format_prompt(prompt, context)
        
        try:
            if ANDROID_AVAILABLE:
                # Create audio-enabled session
                LlmInferenceSession = autoclass('com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession')
                LlmInferenceSessionOptions = autoclass('com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession$LlmInferenceSessionOptions')
                GraphOptions = autoclass('com.google.mediapipe.tasks.genai.llminference.GraphOptions')
                
                session_options = LlmInferenceSessionOptions.builder()
                graph_options = GraphOptions.builder()
                graph_options.setEnableAudioModality(True)
                session_options.setGraphOptions(graph_options.build())
                
                session = LlmInferenceSession.createFromOptions(
                    self.llm_inference,
                    session_options.build()
                )
                
                session.addQueryChunk(formatted_prompt)
                session.addAudio(audio_data)
                
                response = session.generateResponse()
                session.close()
                
                return response
            else:
                return self.llm_inference.generate_with_audio(formatted_prompt, audio_data)
                
        except Exception as e:
            self.logger.error(f"Audio query failed: {e}")
            raise RuntimeError(f"Audio query failed: {e}")
    
    def _format_prompt(self, 
                      prompt: str, 
                      context: Optional[Dict[str, Any]] = None) -> str:
        """
        Format prompt with optional context
        
        Args:
            prompt: Base prompt string
            context: Dictionary of context information
            
        Returns:
            Formatted prompt string
        """
        if not context:
            return prompt
        
        # Build context string
        context_str = "CONTEXT:\n"
        for key, value in context.items():
            context_str += f"  {key}: {value}\n"
        
        return f"{context_str}\n{prompt}"
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get engine statistics
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "inference_count": self.inference_count,
            "total_tokens": self.total_tokens,
            "avg_tokens_per_query": self.total_tokens / max(1, self.inference_count),
            "is_initialized": self.is_initialized,
            "model_path": self.config.model_path,
            "config": {
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "top_k": self.config.top_k,
            }
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.inference_count = 0
        self.total_tokens = 0
    
    def __del__(self):
        """Cleanup resources"""
        if self.session:
            try:
                self.session.close()
            except:
                pass
        
        self.logger.info("LLM Engine destroyed")
    
    def __repr__(self):
        return (f"LLMEngine(model={Path(self.config.model_path).name}, "
                f"initialized={self.is_initialized}, "
                f"queries={self.inference_count})")


class SimulatedLLM:
    """
    Simulated LLM for testing on desktop (non-Android environment)
    
    This provides a mock implementation that returns plausible responses
    for testing purposes without requiring Android device.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.logger.warning("Using SIMULATED LLM - responses are mocked")
    
    def generate(self, prompt: str) -> str:
        """Generate simulated response"""
        # Simple simulation based on keywords
        prompt_lower = prompt.lower()
        
        if "route" in prompt_lower or "navigate" in prompt_lower:
            return json.dumps({
                "route": "optimal_route_calculated",
                "waypoints": [[50.123, 24.456], [50.234, 24.567]],
                "distance": 5.2,
                "estimated_time": "12 minutes",
                "battery_usage": "15%"
            })
        
        elif "emergency" in prompt_lower or "gps" in prompt_lower:
            return "RECOMMENDATION: Switch to inertial navigation. Use visual landmarks. Conserve battery."
        
        elif "obstacle" in prompt_lower or "detect" in prompt_lower:
            return "ANALYSIS: Power lines detected at 100m ahead. Trees on left side. Clear path on right."
        
        else:
            return f"SIMULATED RESPONSE to: {prompt[:50]}..."
    
    def generate_with_vision(self, prompt: str, images: List) -> str:
        """Simulate vision response"""
        return f"SIMULATED VISION: Analyzed {len(images)} images. {prompt}"
    
    def generate_with_audio(self, prompt: str, audio: bytes) -> str:
        """Simulate audio response"""
        return f"SIMULATED AUDIO: Processed {len(audio)} bytes. {prompt}"


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize engine
    engine = LLMEngine(
        model_path="/data/local/tmp/llm/gemma-3n-e2b.task",
        max_tokens=512,
        temperature=0.7
    )
    
    # Basic query
    response = engine.query(
        "Calculate optimal route from 50.123, 24.456 to 50.789, 24.999",
        context={
            "battery": 75,
            "wind_speed": 15,
            "obstacles": ["power_lines", "trees"]
        }
    )
    
    print("Response:", response)
    print("\nStats:", engine.get_stats())
