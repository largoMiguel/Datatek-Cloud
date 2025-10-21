from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User
from app.schemas.user import TokenData

# Configuración de encriptación
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=12
)
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    try:
        # Verificar que el hash no esté vacío y tenga formato válido
        if not hashed_password or len(hashed_password) < 10:
            return False
        
        # Si es un hash fallback, usar verificación manual
        if hashed_password.startswith("fallback:"):
            import hashlib
            parts = hashed_password.split(":")
            if len(parts) != 3:
                return False
            stored_hash, salt = parts[1], parts[2]
            computed_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000).hex()
            return computed_hash == stored_hash
        
        # Usar bcrypt para hashes normales
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Error verificando contraseña: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generar hash de contraseña"""
    try:
        # Asegurar que la contraseña no exceda el límite de bcrypt (72 bytes)
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                # Truncar a 72 bytes de manera segura
                password = password_bytes[:72].decode('utf-8', errors='ignore')
        
        # Generar hash con bcrypt
        hash_result = pwd_context.hash(password)
        return hash_result
    except Exception as e:
        print(f"Error generando hash con bcrypt: {e}")
        # Fallback solo si bcrypt falla completamente
        import hashlib
        import secrets
        # Usar solo los primeros 72 caracteres para el fallback también
        password_safe = password[:72] if len(password) > 72 else password
        salt = secrets.token_hex(16)
        hash_value = hashlib.pbkdf2_hmac('sha256', password_safe.encode('utf-8'), salt.encode(), 100000).hex()
        return f"fallback:{hash_value}:{salt}"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verificar token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    return token_data

def get_current_user(db: Session = Depends(get_db), token_data: TokenData = Depends(verify_token)):
    """Obtener usuario actual desde el token"""
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Obtener usuario activo actual"""
    return current_user

def require_admin(current_user: User = Depends(get_current_active_user)):
    """Requerir que el usuario sea administrador"""
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes"
        )
    return current_user