# 🚀 Guía de Despliegue en AWS - Sistema PQRS Alcaldía

Esta guía te llevará paso a paso para desplegar tu aplicación en Amazon Web Services (AWS).

## 📋 Arquitectura del Despliegue

```
┌─────────────────────────────────────────────────────────┐
│                    AWS CLOUD                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │   S3 Bucket  │      │     EC2      │               │
│  │  (Frontend)  │◄────►│  (Backend)   │               │
│  │   Angular    │      │   FastAPI    │               │
│  └──────────────┘      └──────┬───────┘               │
│         │                      │                        │
│         │              ┌───────▼────────┐              │
│         │              │   RDS          │              │
│         │              │  PostgreSQL    │              │
│         │              └────────────────┘              │
│         │                                               │
│  ┌──────▼───────┐                                      │
│  │  CloudFront  │  (Opcional para HTTPS)               │
│  │   (CDN)      │                                      │
│  └──────────────┘                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Opción 1: Despliegue Rápido (Recomendado para Comenzar)

### Backend en EC2 + Frontend en S3 + RDS PostgreSQL

---

## 📦 PARTE 1: PREPARAR BASE DE DATOS (AWS RDS)

### Paso 1.1: Crear Base de Datos PostgreSQL en RDS

1. **Acceder a AWS Console**
   - Inicia sesión en https://console.aws.amazon.com
   - Busca "RDS" en la barra de búsqueda

2. **Crear Base de Datos**
   - Click en "Create database"
   - Selecciona: **Standard create**
   - Engine: **PostgreSQL**
   - Version: **PostgreSQL 15.x** (última estable)
   
3. **Templates**
   - Selecciona: **Free tier** (si aplicas) o **Production**

4. **Settings**
   ```
   DB instance identifier: pqrs-alcaldia-db
   Master username: pqrsadmin
   Master password: [Genera una contraseña segura]
   ```
   **⚠️ IMPORTANTE: Guarda estas credenciales en un lugar seguro**

5. **Instance Configuration**
   - DB instance class: `db.t3.micro` (Free tier) o `db.t3.small`
   
6. **Storage**
   - Storage type: **General Purpose SSD (gp3)**
   - Allocated storage: **20 GB** (mínimo)
   - Enable storage autoscaling: ✅

7. **Connectivity**
   - VPC: (default)
   - Public access: **Yes** (cambiar a No después si usas VPC)
   - VPC security group: **Create new** → `pqrs-db-sg`
   
8. **Additional Configuration**
   - Initial database name: `pqrs_db`
   - Backup: Enable automatic backups (7 días retención)
   
9. **Click "Create database"** (toma 5-10 minutos)

### Paso 1.2: Configurar Security Group de RDS

1. Ve a **EC2 → Security Groups**
2. Encuentra `pqrs-db-sg`
3. **Inbound Rules** → Edit
4. Agregar regla:
   ```
   Type: PostgreSQL
   Protocol: TCP
   Port: 5432
   Source: 0.0.0.0/0 (temporal - restringir después al security group de EC2)
   ```

### Paso 1.3: Obtener Endpoint de la Base de Datos

1. En RDS Dashboard, selecciona tu base de datos
2. Copia el **Endpoint** (algo como: `pqrs-alcaldia-db.xxxxxx.us-east-1.rds.amazonaws.com`)
3. Guarda este endpoint para usarlo después

---

## 🖥️ PARTE 2: DESPLEGAR BACKEND EN EC2

### Paso 2.1: Crear Instancia EC2

1. **Acceder a EC2**
   - En AWS Console, busca "EC2"
   - Click en "Launch Instance"

2. **Configuración de la Instancia**
   ```
   Name: pqrs-backend-server
   
   Application and OS Images:
   - Ubuntu Server 22.04 LTS (Free tier eligible)
   
   Instance type:
   - t2.micro (Free tier) o t2.small
   
   Key pair:
   - Create new key pair
   - Name: pqrs-backend-key
   - Type: RSA
   - Format: .pem
   - ⚠️ DESCARGA Y GUARDA EL ARCHIVO .pem
   ```

3. **Network Settings**
   - Create security group: `pqrs-backend-sg`
   - Allow SSH from: **My IP**
   - Allow HTTP: **Anywhere** (0.0.0.0/0)
   - Allow HTTPS: **Anywhere** (0.0.0.0/0)
   - Add rule: Custom TCP, Port 8000, Source: Anywhere

4. **Storage**
   - 20 GB gp3

5. **Click "Launch Instance"**

### Paso 2.2: Conectar a la Instancia EC2

```bash
# Cambiar permisos del archivo .pem
chmod 400 ~/Downloads/pqrs-backend-key.pem

# Conectar vía SSH
ssh -i ~/Downloads/pqrs-backend-key.pem ubuntu@<IP-PUBLICA-EC2>
```

### Paso 2.3: Instalar Dependencias en EC2

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Instalar dependencias del sistema
sudo apt install -y postgresql-client libpq-dev git nginx

# Instalar pip
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.11

# Verificar instalación
python3.11 --version
```

### Paso 2.4: Clonar y Configurar el Proyecto

```bash
# Clonar repositorio
cd /home/ubuntu
git clone git@github.com:largoMiguel/Datatek-Cloud.git pqrs-app

# O si no tienes SSH configurado:
# git clone https://github.com/largoMiguel/Datatek-Cloud.git pqrs-app

cd pqrs-app/backend

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 2.5: Configurar Variables de Entorno

```bash
# Crear archivo .env
nano .env
```

Pega el siguiente contenido (reemplaza con tus valores):

```env
# Base de datos PostgreSQL RDS
DATABASE_URL=postgresql://pqrsadmin:TU_PASSWORD@pqrs-alcaldia-db.xxxxxx.us-east-1.rds.amazonaws.com:5432/pqrs_db

# JWT - GENERA UNA CLAVE SEGURA
SECRET_KEY=tu-clave-super-segura-de-64-caracteres-minimo-generada
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=tu-api-key-de-openai

# Servidor
HOST=0.0.0.0
PORT=8000

# CORS - Agregar dominio del frontend
ALLOWED_ORIGINS=http://localhost:4200,https://tu-frontend.s3-website.amazonaws.com

# Producción
ENVIRONMENT=production
DEBUG=False
```

Guardar: `Ctrl + X`, `Y`, `Enter`

**🔐 Generar SECRET_KEY segura:**
```bash
python3.11 -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Paso 2.6: Inicializar Base de Datos

```bash
# Activar entorno virtual si no está activo
source venv/bin/activate

# Iniciar aplicación temporalmente para crear tablas
python3.11 -c "from app.main import app; print('Base de datos inicializada')"
```

### Paso 2.7: Configurar Systemd Service

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/pqrs-backend.service
```

Contenido:

```ini
[Unit]
Description=PQRS Alcaldia Backend API
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/pqrs-app/backend
Environment="PATH=/home/ubuntu/pqrs-app/backend/venv/bin"
ExecStart=/home/ubuntu/pqrs-app/backend/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 app.main:app --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar e iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable pqrs-backend
sudo systemctl start pqrs-backend

# Verificar estado
sudo systemctl status pqrs-backend

# Ver logs
sudo journalctl -u pqrs-backend -f
```

### Paso 2.8: Configurar Nginx como Reverse Proxy (Opcional pero Recomendado)

```bash
# Crear configuración de Nginx
sudo nano /etc/nginx/sites-available/pqrs-backend
```

Contenido:

```nginx
server {
    listen 80;
    server_name api.tu-dominio.com;  # O la IP pública de EC2

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/pqrs-backend /etc/nginx/sites-enabled/

# Probar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx

# Habilitar Nginx al inicio
sudo systemctl enable nginx
```

### Paso 2.9: Verificar Backend

```bash
# Desde EC2
curl http://localhost:8000/health

# Desde tu computadora
curl http://<IP-PUBLICA-EC2>/health
```

Deberías ver: `{"status":"healthy"}`

---

## 🌐 PARTE 3: DESPLEGAR FRONTEND EN S3

### Paso 3.1: Compilar Frontend para Producción

**En tu computadora local:**

```bash
# Ir al directorio del frontend
cd /Users/largo/Documents/SOLUCTIONS/pqrs-alcaldia/frontend/pqrs-frontend

# Actualizar environment.prod.ts con la URL del backend
nano src/environments/environment.prod.ts
```

Actualizar con la IP pública de EC2:

```typescript
export const environment = {
  production: true,
  apiUrl: 'http://<IP-PUBLICA-EC2>:8000/api',  // O http://api.tu-dominio.com/api
  openaiApiKey: ''
};
```

```bash
# Compilar para producción
npm run build:prod

# Los archivos compilados estarán en: dist/pqrs-frontend/browser/
```

### Paso 3.2: Crear Bucket S3

1. **Ir a S3 en AWS Console**
2. **Create bucket**
   ```
   Bucket name: pqrs-alcaldia-frontend (debe ser único globalmente)
   Region: us-east-1 (o tu región preferida)
   ```

3. **Block Public Access settings**
   - ⚠️ **Desmarcar** "Block all public access"
   - Confirmar que entiendes

4. **Click "Create bucket"**

### Paso 3.3: Configurar Bucket para Hosting Estático

1. Selecciona tu bucket
2. Ve a **Properties**
3. Scroll down hasta **Static website hosting**
4. Click **Edit**
   ```
   Static website hosting: Enable
   Hosting type: Host a static website
   Index document: index.html
   Error document: index.html
   ```
5. **Save changes**
6. Copia la **Bucket website endpoint** (ej: http://pqrs-alcaldia-frontend.s3-website-us-east-1.amazonaws.com)

### Paso 3.4: Configurar Política del Bucket

1. Ve a **Permissions**
2. Scroll down hasta **Bucket policy**
3. Click **Edit**
4. Pega esta política (reemplaza `pqrs-alcaldia-frontend` con tu bucket):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::pqrs-alcaldia-frontend/*"
        }
    ]
}
```

5. **Save changes**

### Paso 3.5: Subir Archivos al Bucket

**Opción A: Usando AWS Console (GUI)**

1. Ve a tu bucket
2. Click **Upload**
3. Arrastra todos los archivos de `dist/pqrs-frontend/browser/`
4. Click **Upload**

**Opción B: Usando AWS CLI (Recomendado)**

```bash
# Instalar AWS CLI si no lo tienes
# macOS:
brew install awscli

# Configurar credenciales
aws configure
# Ingresa:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output format: json

# Subir archivos
cd frontend/pqrs-frontend
aws s3 sync dist/pqrs-frontend/browser/ s3://pqrs-alcaldia-frontend/ --delete

# Invalidar caché (si usas CloudFront después)
# aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Paso 3.6: Probar el Frontend

Abre en tu navegador:
```
http://pqrs-alcaldia-frontend.s3-website-us-east-1.amazonaws.com
```

---

## 🔒 PARTE 4: CONFIGURAR HTTPS CON CERTIFICADO SSL (Opcional)

### Opción A: Usar CloudFront + Certificate Manager

1. **Solicitar Certificado SSL**
   - Ve a **AWS Certificate Manager**
   - **Request certificate**
   - Domain name: `tu-dominio.com` y `*.tu-dominio.com`
   - Validation method: DNS
   - Sigue instrucciones para validar dominio

2. **Crear Distribución CloudFront**
   - Ve a **CloudFront**
   - **Create distribution**
   - Origin domain: tu bucket S3
   - Viewer protocol policy: Redirect HTTP to HTTPS
   - Alternate domain names: `tu-dominio.com`
   - Custom SSL certificate: Selecciona tu certificado
   - Default root object: `index.html`

3. **Configurar Manejo de Errores**
   - En la distribución, ve a **Error pages**
   - Create custom error response:
     - HTTP error code: 403, 404
     - Customize error response: Yes
     - Response page path: `/index.html`
     - HTTP response code: 200

4. **Configurar DNS**
   - En tu proveedor de DNS (Route 53, Cloudflare, etc.)
   - Crear registro CNAME:
     ```
     Type: CNAME
     Name: www
     Value: [CloudFront Distribution Domain]
     ```

### Opción B: Usar Certbot en EC2 (para backend)

```bash
# En EC2
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d api.tu-dominio.com

# Renovación automática ya está configurada
```

---

## 📝 PARTE 5: ACTUALIZAR CORS EN BACKEND

Después de desplegar el frontend, actualiza CORS:

```bash
# En EC2
cd /home/ubuntu/pqrs-app/backend
nano .env
```

Actualiza:
```env
ALLOWED_ORIGINS=https://tu-dominio.com,http://pqrs-alcaldia-frontend.s3-website-us-east-1.amazonaws.com
```

```bash
# Reiniciar servicio
sudo systemctl restart pqrs-backend
```

---

## 🔄 PARTE 6: DESPLIEGUES FUTUROS (CI/CD Básico)

### Script para Actualizar Backend

Crear en EC2:

```bash
nano /home/ubuntu/update-backend.sh
```

Contenido:

```bash
#!/bin/bash
cd /home/ubuntu/pqrs-app
git pull origin master
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart pqrs-backend
echo "Backend actualizado!"
```

```bash
chmod +x /home/ubuntu/update-backend.sh
```

### Script para Actualizar Frontend

En tu máquina local:

```bash
nano deploy-frontend.sh
```

Contenido:

```bash
#!/bin/bash
cd frontend/pqrs-frontend
npm run build:prod
aws s3 sync dist/pqrs-frontend/browser/ s3://pqrs-alcaldia-frontend/ --delete
echo "Frontend desplegado!"
```

```bash
chmod +x deploy-frontend.sh
```

---

## ✅ CHECKLIST FINAL

- [ ] Base de datos RDS PostgreSQL funcionando
- [ ] Security groups configurados correctamente
- [ ] Backend en EC2 respondiendo en `/health`
- [ ] Frontend en S3 cargando correctamente
- [ ] CORS configurado con URLs correctas
- [ ] Usuario admin creado (admin/admin123)
- [ ] SSL configurado (opcional pero recomendado)
- [ ] Backups automáticos de RDS habilitados
- [ ] Logs monitoreándose con `journalctl`

---

## 🐛 TROUBLESHOOTING

### Backend no inicia

```bash
# Ver logs detallados
sudo journalctl -u pqrs-backend -n 100 --no-pager

# Verificar proceso
ps aux | grep gunicorn

# Reiniciar servicio
sudo systemctl restart pqrs-backend
```

### No se conecta a la base de datos

```bash
# Probar conexión desde EC2
psql -h pqrs-alcaldia-db.xxxxxx.rds.amazonaws.com -U pqrsadmin -d pqrs_db

# Verificar security group de RDS permite conexión desde EC2
```

### Frontend no carga

```bash
# Verificar permisos del bucket
aws s3api get-bucket-policy --bucket pqrs-alcaldia-frontend

# Verificar que los archivos se subieron
aws s3 ls s3://pqrs-alcaldia-frontend/
```

### Error CORS

- Verifica que `ALLOWED_ORIGINS` en `.env` incluya la URL del frontend
- Reinicia el backend después de cambiar CORS

---

## 💰 COSTOS ESTIMADOS (Región us-east-1)

- **EC2 t2.micro**: $0/mes (Free tier por 12 meses) o ~$8.50/mes
- **RDS db.t3.micro**: $0/mes (Free tier por 12 meses) o ~$15/mes
- **S3**: ~$0.50/mes (para sitio estático pequeño)
- **CloudFront** (opcional): ~$1-5/mes
- **Data Transfer**: Variable según tráfico

**Total estimado**: $0-30/mes dependiendo de si aplicas Free Tier

---

## 📚 RECURSOS ADICIONALES

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [AWS S3 Static Website](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Angular Deployment](https://angular.io/guide/deployment)

---

¡Éxito con tu despliegue! 🚀
