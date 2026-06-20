from fastapi import HTTPException, status

class TenantNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested ISP/Tenant was not found or is inactive."
        )

class PaymentVerificationError(HTTPException):
    def __init__(self, detail: str = "Payment could not be verified."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class RouterConnectionError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The router is currently offline or unreachable."
        )