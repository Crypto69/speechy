"""Ollama API client for LLM interactions."""

import requests
import json
import logging
import time
from typing import Optional, Dict, Any, List, Callable
import threading

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model: str = "llama3.2:3b", timeout: int = 30):
        """Initialize Ollama client.
        
        Args:
            base_url: Base URL for Ollama API
            model: Default model to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.session = requests.Session()
        
        # API endpoints
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        self.models_url = f"{self.base_url}/api/tags"
        self.pull_url = f"{self.base_url}/api/pull"
        self.show_url = f"{self.base_url}/api/show"
        
    def is_server_available(self) -> bool:
        """Check if Ollama server is available.
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama server not available: {e}")
            return False
    
    def list_models(self) -> Optional[List[Dict[str, Any]]]:
        """List available models.
        
        Returns:
            List of model information or None if request failed
        """
        try:
            response = self.session.get(self.models_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get('models', [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return None
    
    def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """Check if a specific model is available.
        
        Args:
            model_name: Model name to check, uses default if None
            
        Returns:
            True if model is available, False otherwise
        """
        model_to_check = model_name or self.model
        models = self.list_models()
        
        if models is None:
            return False
        
        for model in models:
            if model.get('name') == model_to_check:
                return True
        
        return False
    
    def pull_model(self, model_name: str, callback: Optional[Callable[[str], None]] = None) -> bool:
        """Pull/download a model.
        
        Args:
            model_name: Name of model to pull
            callback: Optional callback for progress updates
            
        Returns:
            True if model was pulled successfully, False otherwise
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            
            payload = {"name": model_name}
            response = self.session.post(
                self.pull_url, 
                json=payload, 
                timeout=300,  # 5 minutes for model download
                stream=True
            )
            response.raise_for_status()
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        status = data.get('status', '')
                        
                        if callback:
                            callback(status)
                        
                        logger.info(f"Pull status: {status}")
                        
                        if data.get('error'):
                            logger.error(f"Pull error: {data['error']}")
                            return False
                            
                    except json.JSONDecodeError:
                        continue
            
            logger.info(f"Model {model_name} pulled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    def generate_response(self, prompt: str, model: Optional[str] = None,
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: Optional[int] = None) -> Optional[str]:
        """Generate response from the LLM.
        
        Args:
            prompt: User prompt
            model: Model to use, uses default if None
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response or None if request failed
        """
        model_to_use = model or self.model
        
        try:
            # Prepare the prompt with system message if provided
            if system_prompt:
                formatted_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            else:
                formatted_prompt = prompt
            
            payload = {
                "model": model_to_use,
                "prompt": formatted_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            logger.info(f"Generating response with model: {model_to_use}")
            start_time = time.time()
            
            response = self.session.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get('response', '').strip()
            
            end_time = time.time()
            duration = end_time - start_time
            
            if generated_text:
                logger.info(f"Response generated in {duration:.2f}s: '{generated_text[:100]}{'...' if len(generated_text) > 100 else ''}'")
            else:
                logger.warning("Empty response from LLM")
            
            return generated_text if generated_text else None
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return None
    
    def generate_response_async(self, prompt: str, callback: Callable[[Optional[str]], None],
                              model: Optional[str] = None, system_prompt: Optional[str] = None,
                              temperature: float = 0.7, max_tokens: Optional[int] = None) -> None:
        """Generate response asynchronously.
        
        Args:
            prompt: User prompt
            callback: Function to call with the response
            model: Model to use, uses default if None
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        def generate_worker():
            result = self.generate_response(
                prompt, model, system_prompt, temperature, max_tokens
            )
            callback(result)
        
        thread = threading.Thread(target=generate_worker)
        thread.daemon = True
        thread.start()
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None,
                       temperature: float = 0.7) -> Optional[str]:
        """Chat completion using conversation format.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model to use, uses default if None
            temperature: Sampling temperature
            
        Returns:
            Generated response or None if request failed
        """
        model_to_use = model or self.model
        
        try:
            payload = {
                "model": model_to_use,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            logger.info(f"Chat completion with model: {model_to_use}")
            
            response = self.session.post(
                self.chat_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            message = result.get('message', {})
            content = message.get('content', '').strip()
            
            return content if content else None
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return None
    
    def get_model_info(self, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get information about a specific model.
        
        Args:
            model_name: Model name, uses default if None
            
        Returns:
            Model information or None if request failed
        """
        model_to_check = model_name or self.model
        
        try:
            payload = {"name": model_to_check}
            response = self.session.post(
                self.show_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get model info for {model_to_check}: {e}")
            return None
    
    def set_model(self, model_name: str) -> None:
        """Set the default model.
        
        Args:
            model_name: Name of the model to use as default
        """
        self.model = model_name
        logger.info(f"Default model set to: {model_name}")
    
    def get_current_model(self) -> str:
        """Get the current default model.
        
        Returns:
            Current default model name
        """
        return self.model