"""
术语表API
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from app.models.request import GlossaryUpdateRequest, GlossaryItemRequest
from app.models.response import GlossaryResponse
from app.services.glossary_service import glossary_service
from app.config import security_config

router = APIRouter(prefix="/api/v1", tags=["glossary"])

# 速率限制
limiter = Limiter(key_func=get_remote_address)


@router.get("/glossary", response_model=GlossaryResponse)
@limiter.limit(security_config.RATE_LIMIT_GLOSSARY)
async def get_glossary(request: Request):
    """
    获取术语表
    """
    try:
        glossary = await glossary_service.load()
        return GlossaryResponse(glossary=glossary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/glossary", response_model=GlossaryResponse)
@limiter.limit(security_config.RATE_LIMIT_GLOSSARY)
async def update_glossary(request: Request, glossary_request: GlossaryUpdateRequest):
    """
    更新术语表
    """
    try:
        await glossary_service.save(glossary_request.glossary)
        return GlossaryResponse(glossary=glossary_request.glossary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/glossary/{term}")
@limiter.limit(security_config.RATE_LIMIT_GLOSSARY)
async def update_term(request: Request, term: str, item: GlossaryItemRequest):
    """
    更新单个术语
    """
    try:
        await glossary_service.update(term, item.translation)
        return {"message": "更新成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/glossary/{term}")
@limiter.limit(security_config.RATE_LIMIT_GLOSSARY)
async def delete_term(request: Request, term: str):
    """
    删除术语
    """
    try:
        success = await glossary_service.delete(term)
        if not success:
            raise HTTPException(status_code=404, detail="术语不存在")
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

