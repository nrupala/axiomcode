"""
AutoCoder Integration Layer
===========================
Connects UIS, SLM, and AxiomCode services.
"""

import os
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    name: str
    url: str
    port: int
    status: str = "unknown"


class ServiceRegistry:
    """Registry of all AutoCoder ecosystem services."""
    
    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self._register_default_services()
    
    def _register_default_services(self):
        """Register known services."""
        # AutoCoder itself
        self.register("autocoder", "http://localhost:5000", 5000)
        
        # UIS - Unified Intelligence System
        self.register("uis", "http://localhost:8000", 8000)
        
        # SLM - Self-Learning Model
        self.register("slm", "http://localhost:8080", 8080)
        
        # AxiomCode - Mathematical code verification
        self.register("axiomcode", "http://localhost:9000", 9000)
        
        # Ollama for local models
        self.register("ollama", "http://localhost:11434", 11434)
        
        # LM Studio
        self.register("lmstudio", "http://localhost:1234", 1234)
    
    def register(self, name: str, url: str, port: int):
        """Register a service."""
        self.services[name] = ServiceConfig(name=name, url=url, port=port)
        logger.info(f"Registered service: {name} at {url}")
    
    def get(self, name: str) -> Optional[ServiceConfig]:
        """Get a service by name."""
        return self.services.get(name)
    
    def get_url(self, name: str) -> Optional[str]:
        """Get service URL."""
        svc = self.services.get(name)
        return svc.url if svc else None
    
    def list_services(self) -> Dict[str, ServiceConfig]:
        """List all registered services."""
        return self.services.copy()
    
    def check_health(self, name: str) -> bool:
        """Check if a service is healthy."""
        import requests
        svc = self.services.get(name)
        if not svc:
            return False
        try:
            resp = requests.get(f"{svc.url}/health", timeout=2)
            return resp.status_code == 200
        except:
            return False


class CodeOrchestrator:
    """Orchestrates code generation across services."""
    
    def __init__(self):
        self.registry = ServiceRegistry()
    
    def generate_code(self, prompt: str, verify: bool = False) -> Dict[str, Any]:
        """Generate and optionally verify code."""
        result = {"prompt": prompt, "code": None, "verified": False, "errors": []}
        
        # Use local engine first (fastest)
        from engine import generate
        try:
            result["code"] = generate(prompt)
            logger.info(f"Generated code for: {prompt[:50]}...")
        except Exception as e:
            result["errors"].append(f"Generation failed: {e}")
        
        # Optionally verify with AxiomCode
        if verify and result["code"]:
            # TODO: Connect to axiomcode
            pass
        
        return result
    
    def chat_with_context(self, message: str, context: str = "") -> str:
        """Chat with UIS for context-aware responses."""
        # TODO: Connect to UIS
        return f"Response to: {message}"


# Global instances
registry = ServiceRegistry()
orchestrator = CodeOrchestrator()


def get_service(name: str) -> Optional[ServiceConfig]:
    return registry.get(name)

def list_all_services() -> Dict[str, ServiceConfig]:
    return registry.list_services()

def generate_code(prompt: str, verify: bool = False) -> Dict[str, Any]:
    return orchestrator.generate_code(prompt, verify)