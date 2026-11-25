class Role:
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class OrderStatus:
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ActionType:
    CREATE_ORDER = "create_order"
    CANCEL_ORDER = "cancel_order"


class ActionStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class ChatMode:
    GENERAL = "GENERAL"
    RAG = "RAG"
    AGENT = "AGENT"
    MIXED = "MIXED"


class MessageRole:
    USER = "user"
    ASSISTANT = "assistant"


class DocumentStatus:
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
