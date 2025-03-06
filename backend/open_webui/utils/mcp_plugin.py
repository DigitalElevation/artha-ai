"""
name: MCP Server Plugin
description: Plugin para adicionar suporte a servidores MCP (Model Control Protocol) no Open WebUI
version: 0.1.0
author: Artha Intelligence
requirements: requests
"""

import logging
import json
import requests
from typing import Dict, List, Optional, Any

from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.models import ModelMeta, ModelParams

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

class MCPServerPlugin:
    """
    Plugin para gerenciar servidores MCP (Model Control Protocol) no Open WebUI.
    """
    
    def __init__(self):
        self.name = "MCP Server Plugin"
        self.description = "Plugin para adicionar suporte a servidores MCP (Model Control Protocol) no Open WebUI"
        self.version = "0.1.0"
    
    def verify_connection(self, url: str, api_key: Optional[str] = None) -> bool:
        """
        Verifica a conexão com um servidor MCP.
        
        Args:
            url: URL do servidor MCP
            api_key: Chave de API opcional para autenticação
            
        Returns:
            bool: True se a conexão for bem-sucedida, False caso contrário
        """
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.get(f"{url}/v1/models", headers=headers, timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            log.error(f"Erro ao conectar ao servidor MCP: {e}")
            return False
    
    def get_models(self, url: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtém a lista de modelos disponíveis em um servidor MCP.
        
        Args:
            url: URL do servidor MCP
            api_key: Chave de API opcional para autenticação
            
        Returns:
            List[Dict[str, Any]]: Lista de modelos disponíveis
        """
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.get(f"{url}/v1/models", headers=headers, timeout=10)
            response.raise_for_status()
            
            models_data = response.json().get("data", [])
            
            # Formatar os modelos para o formato esperado pelo Open WebUI
            formatted_models = []
            for model in models_data:
                formatted_model = {
                    "id": model.get("id", ""),
                    "name": model.get("name", model.get("id", "")),
                    "object": "model",
                    "created": model.get("created", 0),
                    "owned_by": "mcp",
                    "mcp": model,
                    "meta": {
                        "profile_image_url": "/static/favicon.png",
                        "description": model.get("description", "Modelo MCP"),
                        "capabilities": {
                            "chat": True,
                            "vision": model.get("capabilities", {}).get("vision", False),
                            "tools": model.get("capabilities", {}).get("tools", False),
                        }
                    }
                }
                formatted_models.append(formatted_model)
            
            return formatted_models
        except Exception as e:
            log.error(f"Erro ao obter modelos do servidor MCP: {e}")
            return []
    
    def create_chat_completion(self, url: str, api_key: Optional[str] = None, 
                              model: str = "", messages: List[Dict[str, str]] = None, 
                              stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Cria uma conclusão de chat usando um modelo MCP.
        
        Args:
            url: URL do servidor MCP
            api_key: Chave de API opcional para autenticação
            model: ID do modelo a ser usado
            messages: Lista de mensagens para o chat
            stream: Se True, a resposta será transmitida
            **kwargs: Parâmetros adicionais para a API
            
        Returns:
            Dict[str, Any]: Resposta da API
        """
        if messages is None:
            messages = []
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                **kwargs
            }
            
            response = requests.post(
                f"{url}/v1/chat/completions", 
                headers=headers,
                json=payload,
                stream=stream,
                timeout=60
            )
            response.raise_for_status()
            
            if stream:
                return response.iter_lines()
            else:
                return response.json()
        except Exception as e:
            log.error(f"Erro ao criar chat completion com servidor MCP: {e}")
            raise e
    
    def get_model_config_template(self) -> Dict[str, Any]:
        """
        Retorna um template de configuração para servidores MCP.
        
        Returns:
            Dict[str, Any]: Template de configuração
        """
        return {
            "ENABLE_MCP_API": False,
            "MCP_BASE_URLS": [],
            "MCP_API_KEYS": {},
            "MCP_API_CONFIGS": {}
        }
    
    def convert_to_openai_format(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte dados de modelo MCP para o formato OpenAI esperado pelo Open WebUI.
        
        Args:
            model_data: Dados do modelo MCP
            
        Returns:
            Dict[str, Any]: Dados do modelo no formato OpenAI
        """
        return {
            "id": model_data.get("id", ""),
            "name": model_data.get("name", model_data.get("id", "")),
            "object": "model",
            "created": model_data.get("created", 0),
            "owned_by": "mcp",
            "mcp": model_data,
            "meta": ModelMeta(
                profile_image_url="/static/favicon.png",
                description=model_data.get("description", "Modelo MCP"),
                capabilities={
                    "chat": True,
                    "vision": model_data.get("capabilities", {}).get("vision", False),
                    "tools": model_data.get("capabilities", {}).get("tools", False),
                }
            ),
            "params": ModelParams()
        } 