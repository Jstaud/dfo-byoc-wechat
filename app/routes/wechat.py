"""WeChat webhook endpoints."""
from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse, Response
from wechatpy import parse_message
from wechatpy.utils import check_signature
from wechatpy.crypto import WeChatCrypto
from app.config import settings
from app.clients.cxone_client import get_cxone_client
from app.exceptions import ValidationError, CXoneAPIError
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/webhook")
async def wechat_webhook_get(
    signature: str = Query(..., min_length=1, max_length=128),
    timestamp: str = Query(..., min_length=1, max_length=20),
    nonce: str = Query(..., min_length=1, max_length=128),
    echostr: str = Query(..., min_length=1, max_length=128)
):
    """
    WeChat webhook GET endpoint for signature validation.
    
    This is called by WeChat during webhook configuration to verify the endpoint.
    """
    try:
        # Validate signature
        is_valid = check_signature(
            settings.wechat_token,
            signature,
            timestamp,
            nonce
        )
        
        if is_valid:
            logger.info("wechat_webhook_validated", timestamp=timestamp)
            return PlainTextResponse(content=echostr)
        else:
            logger.warning(
                "invalid_wechat_signature",
                signature=signature[:10] + "...",  # Don't log full signature
                timestamp=timestamp,
                nonce=nonce[:10] + "..."
            )
            raise ValidationError("Invalid WeChat signature")
            
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            "wechat_signature_validation_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise ValidationError("Signature validation failed")


@router.post("/webhook")
async def wechat_webhook_post(
    request: Request,
    signature: str = Query(..., min_length=1, max_length=128),
    timestamp: str = Query(..., min_length=1, max_length=20),
    nonce: str = Query(..., min_length=1, max_length=128)
):
    """
    WeChat webhook POST endpoint for receiving messages.
    
    Validates signature, decrypts if needed, parses message, and forwards to CXone.
    """
    try:
        # Validate signature
        is_valid = check_signature(
            settings.wechat_token,
            signature,
            timestamp,
            nonce
        )
        
        if not is_valid:
            logger.warning(
                "invalid_wechat_signature",
                signature=signature[:10] + "...",
                timestamp=timestamp
            )
            raise ValidationError("Invalid WeChat signature")
        
        # Read raw XML body with size limit (prevent DoS)
        body_bytes = await request.body()
        if len(body_bytes) > 100000:  # 100KB limit
            raise ValidationError("Request body too large")
        
        xml_content = body_bytes.decode('utf-8')
        
        # Handle encryption if encoding AES key is configured
        if settings.wechat_encoding_aes_key:
            crypto = WeChatCrypto(
                settings.wechat_token,
                settings.wechat_encoding_aes_key,
                settings.wechat_appid
            )
            # For encrypted messages, WeChat includes msg_signature in query params
            msg_signature = request.query_params.get('msg_signature', '')
            try:
                decrypted_xml = crypto.decrypt_message(
                    xml_content,
                    signature=msg_signature,
                    timestamp=timestamp,
                    nonce=nonce
                )
                xml_content = decrypted_xml
                logger.debug("wechat_message_decrypted")
            except Exception as e:
                logger.error(
                    "wechat_decryption_failed",
                    error=str(e),
                    error_type=type(e).__name__
                )
                # In production, you might want to raise an error instead
                # For now, try parsing as plain message
                pass
        
        # Parse message
        msg = parse_message(xml_content)
        
        logger.info(
            "wechat_message_received",
            msg_type=msg.type,
            source=msg.source,
            msg_id=getattr(msg, 'id', None)
        )
        
        # Handle different message types
        # For now, only handle text messages
        if msg.type == 'text':
            openid = msg.source  # The sender's openid
            text = msg.content   # The message text
            
            if not openid or not text:
                logger.warning(
                    "invalid_wechat_message",
                    has_openid=bool(openid),
                    has_text=bool(text)
                )
                # Return success to WeChat to avoid retries
                return Response(status_code=200)
            
            # Post to CXone
            try:
                cxone_client = await get_cxone_client()
                result = await cxone_client.post_message(openid, text)
                
                logger.info(
                    "wechat_message_forwarded_to_cxone",
                    openid=openid,
                    cxone_id=result.get("id")
                )
            except CXoneAPIError as e:
                logger.error(
                    "failed_to_post_to_cxone",
                    openid=openid,
                    error=str(e),
                    error_details=e.details
                )
                # Return success to WeChat to avoid retries
                # TODO: Implement message queue for retry
            except Exception as e:
                logger.error(
                    "unexpected_error_posting_to_cxone",
                    openid=openid,
                    error=str(e),
                    error_type=type(e).__name__
                )
                # Return success to WeChat to avoid retries
        else:
            logger.info(
                "unsupported_message_type",
                msg_type=msg.type,
                source=msg.source
            )
        
        # Return success response to WeChat (no auto-reply)
        return Response(status_code=200)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.exception(
            "wechat_webhook_processing_error",
            error=str(e),
            error_type=type(e).__name__
        )
        # Return 200 to prevent WeChat from retrying
        # In production, you might want to return 500 for unexpected errors
        return Response(status_code=200)
