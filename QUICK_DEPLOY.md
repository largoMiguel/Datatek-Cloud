# ⚡ Guía Rápida de Despliegue AWS

Esta es una guía resumida para desplegar rápidamente. Para detalles completos, consulta `AWS_DEPLOYMENT_GUIDE.md`.

## 🎯 Pre-requisitos

- [ ] Cuenta de AWS activa
- [ ] AWS CLI instalado (`brew install awscli`)
- [ ] Git configurado con SSH
- [ ] Node.js y npm instalados
- [ ] Acceso a tu repositorio en GitHub

## 🚀 Despliegue en 3 Pasos

### PASO 1: Base de Datos (5-10 min) ⚡

```bash
# En AWS Console:
1. Ir a RDS → Create Database
2. PostgreSQL 15.x, Free tier o Production
3. DB identifier: pqrs-alcaldia-db
4. Username: pqrsadmin, Password: [crear segura]
5. Initial database: pqrs_db
6. Public access: Yes (temporal)
7. Security group: Permitir puerto 5432
8. Create database
9. Copiar endpoint: pqrs-alcaldia-db.xxxxx.us-east-1.rds.amazonaws.com
```

### PASO 2: Backend en EC2 (10-15 min) ⚡

```bash
# En AWS Console:
1. EC2 → Launch Instance
   - Name: pqrs-backend-server
   - Ubuntu 22.04 LTS
   - t2.micro (Free tier)
   - Create key pair → Descargar .pem
   - Security group: SSH (22), HTTP (80), Custom TCP (8000)

# Conectar vía SSH:
ssh -i ~/Downloads/pqrs-backend-key.pem ubuntu@<IP-PUBLICA>

# En EC2, ejecutar:
sudo apt update && sudo apt upgrade -y
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt install -y python3.11 python3.11-venv python3.11-dev postgresql-client libpq-dev git nginx
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11

# Clonar proyecto:
cd /home/ubuntu
git clone git@github.com:largoMiguel/Datatek-Cloud.git pqrs-app
cd pqrs-app/backend

# Setup:
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env:
nano .env
# Pegar:
DATABASE_URL=postgresql://pqrsadmin:PASSWORD@RDS-ENDPOINT:5432/pqrs_db
SECRET_KEY=$(python3.11 -c "import secrets; print(secrets.token_urlsafe(64))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENAI_API_KEY=tu-key
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=http://localhost:4200
ENVIRONMENT=production
DEBUG=False

# Crear servicio:
sudo nano /etc/systemd/system/pqrs-backend.service
# Copiar contenido de AWS_DEPLOYMENT_GUIDE.md sección 2.7

# Iniciar:
sudo systemctl daemon-reload
sudo systemctl enable pqrs-backend
sudo systemctl start pqrs-backend
sudo systemctl status pqrs-backend

# Verificar:
curl http://localhost:8000/health
```

### PASO 3: Frontend en S3 (5-10 min) ⚡

```bash
# En tu máquina local:
cd /Users/largo/Documents/SOLUCTIONS/pqrs-alcaldia

# Configurar AWS CLI:
aws configure
# Ingresar Access Key, Secret Key, region (us-east-1)

# En AWS Console:
1. S3 → Create bucket
   - Name: pqrs-alcaldia-frontend
   - Region: us-east-1
   - Desmarcar "Block all public access"
2. Properties → Static website hosting → Enable
   - Index: index.html
   - Error: index.html
3. Permissions → Bucket policy:
{
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "PublicReadGetObject",
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::pqrs-alcaldia-frontend/*"
    }]
}

# Desplegar con script:
./scripts/deploy-frontend.sh pqrs-alcaldia-frontend http://<EC2-IP>:8000/api

# O manualmente:
cd frontend/pqrs-frontend
# Actualizar src/environments/environment.prod.ts con IP de EC2
npm run build:prod
aws s3 sync dist/pqrs-frontend/browser/ s3://pqrs-alcaldia-frontend/ --delete
```

## ✅ Verificación

```bash
# Verificar backend:
curl http://<EC2-IP>:8000/health

# Verificar frontend:
# Abrir en navegador:
http://pqrs-alcaldia-frontend.s3-website-us-east-1.amazonaws.com

# Login con:
Usuario: admin
Password: admin123
```

## 🔄 Actualizaciones Futuras

```bash
# Actualizar backend:
git push origin master
./scripts/update-backend.sh <EC2-IP> ~/Downloads/pqrs-backend-key.pem

# Actualizar frontend:
git push origin master
./scripts/deploy-frontend.sh pqrs-alcaldia-frontend
```

## 🛡️ Seguridad Post-Despliegue

1. **Cambiar contraseña de admin** (primera vez que entres)
2. **Actualizar CORS en backend**:
   ```bash
   # En EC2:
   nano /home/ubuntu/pqrs-app/backend/.env
   # Cambiar ALLOWED_ORIGINS con URL de S3
   sudo systemctl restart pqrs-backend
   ```
3. **Restringir RDS**: Security group solo desde EC2
4. **Configurar HTTPS**: Usar CloudFront + Certificate Manager
5. **Backups**: Habilitar snapshots automáticos en RDS

## 💰 Costos Estimados

- Free Tier (12 meses): ~$0-5/mes
- Post Free Tier: ~$25-35/mes
  - EC2 t2.micro: ~$8.50
  - RDS db.t3.micro: ~$15
  - S3: ~$0.50
  - Transfer: ~$1-5

## 🆘 Ayuda Rápida

```bash
# Ver logs del backend:
ssh -i ~/pqrs-backend-key.pem ubuntu@<EC2-IP>
sudo journalctl -u pqrs-backend -f

# Reiniciar backend:
sudo systemctl restart pqrs-backend

# Verificar RDS:
psql -h <RDS-ENDPOINT> -U pqrsadmin -d pqrs_db

# Ver archivos en S3:
aws s3 ls s3://pqrs-alcaldia-frontend/
```

## 📚 Documentación Completa

- **Guía Detallada**: `AWS_DEPLOYMENT_GUIDE.md`
- **Scripts**: `scripts/README.md`
- **Proyecto**: `README.md`

---

**🎉 ¡Listo! Tu aplicación está en producción en AWS**
