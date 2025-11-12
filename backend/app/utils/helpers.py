from typing import Dict, List, Any
from datetime import datetime
from bson import ObjectId

def serialize_doc(doc: Dict) -> Dict:
    """
    Serializa un documento de MongoDB convirtiéndolo a JSON-compatible
    """
    if doc is None:
        return None
    
    # Convertir ObjectId a string
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    
    # Convertir datetime a ISO format string
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
        elif isinstance(value, ObjectId):
            doc[key] = str(value)
    
    return doc

def serialize_docs(docs: List[Dict]) -> List[Dict]:
    """
    Serializa múltiples documentos de MongoDB
    """
    return [serialize_doc(doc) for doc in docs]