import logging
import json
import time
from typing import Dict, List, Optional, Any

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS, ENABLE_FORWARD_USER_INFO_HEADERS
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.mcp_plugin import MCPServerPlugin

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

router = APIRouter()
mcp_plugin = MCPServerPlugin()

###########################
# Modelos de dados
###########################

class MCPConfigForm(BaseModel):
    ENABLE_MCP_API: bool
    MCP_BASE_URLS: List[str]
    MCP_API_CONFIGS: Dict[str, Any]
    
    model_config = ConfigDict(extra="allow")

class MCPVerifyForm(BaseModel):
    url: str
    key: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")

class ModelNameForm(BaseModel):
    name: str
    
    model_config = ConfigDict(extra="allow")

###########################
# Endpoints da API
###########################

@router.get("/config")
async def get_config(request: Request, user=Depends(get_admin_user)):
    """
    Obtém a configuração atual dos servidores MCP.
    """
    return {
        "ENABLE_MCP_API": request.app.state.config.ENABLE_MCP_API 
            if hasattr(request.app.state.config, "ENABLE_MCP_API") else False,
        "MCP_BASE_URLS": request.app.state.config.MCP_BASE_URLS 
            if hasattr(request.app.state.config, "MCP_BASE_URLS") else [],
        "MCP_API_CONFIGS": request.app.state.config.MCP_API_CONFIGS 
            if hasattr(request.app.state.config, "MCP_API_CONFIGS") else {},
    }

@router.post("/config/update")
async def update_config(
    request: Request, form_data: MCPConfigForm, user=Depends(get_admin_user)
):
    """
    Atualiza a configuração dos servidores MCP.
    """
    request.app.state.config.ENABLE_MCP_API = form_data.ENABLE_MCP_API
    request.app.state.config.MCP_BASE_URLS = form_data.MCP_BASE_URLS
    request.app.state.config.MCP_API_CONFIGS = form_data.MCP_API_CONFIGS

    # Remove as configurações de API que não estão nas URLs
    keys = list(map(str, range(len(request.app.state.config.MCP_BASE_URLS))))
    request.app.state.config.MCP_API_CONFIGS = {
        key: value
        for key, value in request.app.state.config.MCP_API_CONFIGS.items()
        if key in keys
    }

    return {
        "ENABLE_MCP_API": request.app.state.config.ENABLE_MCP_API,
        "MCP_BASE_URLS": request.app.state.config.MCP_BASE_URLS,
        "MCP_API_CONFIGS": request.app.state.config.MCP_API_CONFIGS,
    }

@router.get("/urls")
async def get_urls(request: Request, user=Depends(get_verified_user)):
    """
    Obtém as URLs dos servidores MCP configurados.
    """
    return {
        "MCP_BASE_URLS": request.app.state.config.MCP_BASE_URLS 
            if hasattr(request.app.state.config, "MCP_BASE_URLS") else []
    }

@router.post("/verify")
async def verify_connection(
    request: Request, form_data: MCPVerifyForm, user=Depends(get_admin_user)
):
    """
    Verifica a conexão com um servidor MCP.
    """
    try:
        result = mcp_plugin.verify_connection(form_data.url, form_data.key)
        if result:
            return {"status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível conectar ao servidor MCP",
            )
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao verificar conexão: {str(e)}",
        )

@router.get("/models")
async def get_all_models(request: Request, user=Depends(get_verified_user)):
    """
    Obtém todos os modelos disponíveis em todos os servidores MCP configurados.
    """
    if not hasattr(request.app.state.config, "ENABLE_MCP_API") or not request.app.state.config.ENABLE_MCP_API:
        return {"models": []}
    
    if not hasattr(request.app.state, "MCP_MODELS"):
        request.app.state.MCP_MODELS = {}
    
    models = []
    
    for idx, url in enumerate(request.app.state.config.MCP_BASE_URLS):
        try:
            api_key = None
            if hasattr(request.app.state.config, "MCP_API_CONFIGS"):
                api_config = request.app.state.config.MCP_API_CONFIGS.get(str(idx), {})
                api_key = api_config.get("api_key", None)
            
            server_models = mcp_plugin.get_models(url, api_key)
            
            # Adiciona o índice da URL para cada modelo
            for model in server_models:
                if "urls" not in model:
                    model["urls"] = []
                model["urls"].append(idx)
                
                # Armazena o modelo no estado da aplicação
                model_id = model["id"]
                if model_id not in request.app.state.MCP_MODELS:
                    request.app.state.MCP_MODELS[model_id] = model
                else:
                    # Se o modelo já existe, apenas adiciona a URL
                    if idx not in request.app.state.MCP_MODELS[model_id]["urls"]:
                        request.app.state.MCP_MODELS[model_id]["urls"].append(idx)
            
            models.extend(server_models)
        except Exception as e:
            log.error(f"Erro ao obter modelos do servidor MCP {url}: {e}")
    
    return {"models": models}

@router.post("/chat/completions")
async def create_chat_completion(
    request: Request, user=Depends(get_verified_user)
):
    """
    Cria uma conclusão de chat usando um modelo MCP.
    """
    if not hasattr(request.app.state.config, "ENABLE_MCP_API") or not request.app.state.config.ENABLE_MCP_API:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API MCP não está habilitada",
        )
    
    try:
        body = await request.json()
        model_id = body.get("model", "")
        
        # Verifica se o modelo existe
        if not hasattr(request.app.state, "MCP_MODELS") or model_id not in request.app.state.MCP_MODELS:
            # Tenta atualizar a lista de modelos
            await get_all_models(request, user=user)
            
            if not hasattr(request.app.state, "MCP_MODELS") or model_id not in request.app.state.MCP_MODELS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Modelo não encontrado: {model_id}",
                )
        
        model = request.app.state.MCP_MODELS[model_id]
        url_idx = model["urls"][0]  # Usa o primeiro servidor disponível
        url = request.app.state.config.MCP_BASE_URLS[url_idx]
        
        api_key = None
        if hasattr(request.app.state.config, "MCP_API_CONFIGS"):
            api_config = request.app.state.config.MCP_API_CONFIGS.get(str(url_idx), {})
            api_key = api_config.get("api_key", None)
        
        # Adiciona informações do usuário nos cabeçalhos, se configurado
        if ENABLE_FORWARD_USER_INFO_HEADERS and user:
            body["user_info"] = {
                "name": user.name,
                "id": user.id,
                "email": user.email,
                "role": user.role,
            }
        
        stream = body.get("stream", False)
        
        # Chama o plugin para criar a conclusão do chat
        response = mcp_plugin.create_chat_completion(
            url=url,
            api_key=api_key,
            model=model_id,
            messages=body.get("messages", []),
            stream=stream,
            **{k: v for k, v in body.items() if k not in ["model", "messages", "stream"]}
        )
        
        if stream:
            # Retorna um streaming response
            async def stream_response():
                for line in response:
                    if line:
                        yield line + b"\n\n"
            
            return StreamingResponse(stream_response(), media_type="text/event-stream")
        else:
            # Retorna a resposta completa
            return response
    except HTTPException:
        raise
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar chat completion: {str(e)}",
        ) 