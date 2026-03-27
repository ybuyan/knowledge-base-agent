"""
Constraint Management API
Manage knowledge base constraints via REST API.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.core.constraint_config import get_constraint_config, ConstraintConfig

router = APIRouter()
logger = logging.getLogger(__name__)


class ConstraintResponse(BaseModel):
    """Response model for constraint configuration"""
    constraints: Dict[str, Any]
    message: str = "Success"


class UpdateConstraintRequest(BaseModel):
    """Request model for updating constraints"""
    retrieval: Optional[Dict[str, Any]] = None
    generation: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    fallback: Optional[Dict[str, Any]] = None


class ConstraintLogEntry(BaseModel):
    """Log entry for constraint checks"""
    timestamp: str
    query: str
    similarity_score: float
    document_count: int
    passed: bool
    reason: str


class ConstraintStatsResponse(BaseModel):
    """Statistics about constraint checks"""
    total_queries: int
    passed_queries: int
    failed_queries: int
    pass_rate: float
    avg_similarity_score: float
    recent_logs: List[ConstraintLogEntry]


@router.get("", response_model=ConstraintResponse)
async def get_constraints():
    """Get current constraint configuration"""
    config = get_constraint_config()
    return ConstraintResponse(
        constraints=config._config.get("constraints", {})
    )


@router.put("", response_model=ConstraintResponse)
async def update_constraints(request: UpdateConstraintRequest):
    """Update constraint configuration"""
    config = get_constraint_config()
    
    try:
        # Update each section if provided
        if request.retrieval is not None:
            config._config["constraints"]["retrieval"].update(request.retrieval)
        
        if request.generation is not None:
            config._config["constraints"]["generation"].update(request.generation)
        
        if request.validation is not None:
            config._config["constraints"]["validation"].update(request.validation)
        
        if request.fallback is not None:
            config._config["constraints"]["fallback"].update(request.fallback)
        
        # Save configuration
        config._save_config()
        
        logger.info("Constraints updated successfully")
        
        return ConstraintResponse(
            constraints=config._config.get("constraints", {}),
            message="Constraints updated successfully"
        )
    except Exception as e:
        logger.error(f"Failed to update constraints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=ConstraintResponse)
async def reset_constraints():
    """Reset constraints to default values"""
    from app.core.constraint_config import DEFAULT_CONSTRAINTS
    
    config = get_constraint_config()
    
    try:
        config._config["constraints"] = DEFAULT_CONSTRAINTS["constraints"]
        config._save_config()
        
        logger.info("Constraints reset to defaults")
        
        return ConstraintResponse(
            constraints=config._config.get("constraints", {}),
            message="Constraints reset to default values"
        )
    except Exception as e:
        logger.error(f"Failed to reset constraints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload", response_model=ConstraintResponse)
async def reload_constraints():
    """
    重新加载配置文件
    
    当配置文件被外部修改后（如前端直接修改文件），
    调用此接口重新加载配置，使修改立即生效。
    """
    config = get_constraint_config()
    
    try:
        success = config.reload()
        
        if success:
            logger.info("Constraints reloaded from file")
            return ConstraintResponse(
                constraints=config._config.get("constraints", {}),
                message="Constraints reloaded successfully from file"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reload constraints"
            )
    except Exception as e:
        logger.error(f"Failed to reload constraints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ConstraintStatsResponse)
async def get_constraint_stats():
    """Get statistics about constraint checks"""
    import os
    import json
    from datetime import datetime, timedelta
    
    log_file = "data/logs/constraints.log"
    
    total_queries = 0
    passed_queries = 0
    failed_queries = 0
    total_similarity = 0.0
    recent_logs = []
    
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line in lines[-100:]:  # Last 100 entries
                    try:
                        entry = json.loads(line.strip())
                        total_queries += 1
                        total_similarity += entry.get("similarity_score", 0)
                        
                        if entry.get("passed", False):
                            passed_queries += 1
                        else:
                            failed_queries += 1
                        
                        if len(recent_logs) < 20:
                            recent_logs.append(ConstraintLogEntry(
                                timestamp=entry.get("timestamp", ""),
                                query=entry.get("query", ""),
                                similarity_score=entry.get("similarity_score", 0),
                                document_count=entry.get("document_count", 0),
                                passed=entry.get("passed", False),
                                reason=entry.get("reason", "")
                            ))
                    except:
                        continue
        except Exception as e:
            logger.error(f"Failed to read constraint logs: {e}")
    
    avg_similarity = total_similarity / total_queries if total_queries > 0 else 0
    pass_rate = passed_queries / total_queries if total_queries > 0 else 0
    
    return ConstraintStatsResponse(
        total_queries=total_queries,
        passed_queries=passed_queries,
        failed_queries=failed_queries,
        pass_rate=round(pass_rate, 2),
        avg_similarity_score=round(avg_similarity, 3),
        recent_logs=recent_logs
    )


@router.get("/retrieval")
async def get_retrieval_constraints():
    """Get retrieval constraints"""
    config = get_constraint_config()
    return config.retrieval


@router.put("/retrieval")
async def update_retrieval_constraints(constraints: Dict[str, Any]):
    """Update retrieval constraints"""
    config = get_constraint_config()
    config._config["constraints"]["retrieval"].update(constraints)
    config._save_config()
    return {"message": "Retrieval constraints updated", "constraints": config.retrieval}


@router.get("/generation")
async def get_generation_constraints():
    """Get generation constraints"""
    config = get_constraint_config()
    return config.generation


@router.put("/generation")
async def update_generation_constraints(constraints: Dict[str, Any]):
    """Update generation constraints"""
    config = get_constraint_config()
    config._config["constraints"]["generation"].update(constraints)
    config._save_config()
    return {"message": "Generation constraints updated", "constraints": config.generation}


@router.get("/validation")
async def get_validation_constraints():
    """Get validation constraints"""
    config = get_constraint_config()
    return config.validation


@router.put("/validation")
async def update_validation_constraints(constraints: Dict[str, Any]):
    """Update validation constraints"""
    config = get_constraint_config()
    config._config["constraints"]["validation"].update(constraints)
    config._save_config()
    return {"message": "Validation constraints updated", "constraints": config.validation}
