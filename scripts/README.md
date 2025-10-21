# 🚀 Scripts de Despliegue

Scripts automatizados para facilitar el despliegue y actualización de la aplicación en AWS.

## 📋 Scripts Disponibles

### 1. `update-backend.sh` - Actualizar Backend en EC2

Actualiza el código del backend en EC2, instala dependencias y reinicia el servicio.

**Uso:**
```bash
./scripts/update-backend.sh <IP-EC2> <PATH-TO-PEM-KEY>
```

**Ejemplo:**
```bash
./scripts/update-backend.sh 54.123.45.67 ~/Downloads/pqrs-backend-key.pem
```

**Lo que hace:**
- Conecta a EC2 vía SSH
- Hace `git pull` del código más reciente
- Instala/actualiza dependencias Python
- Reinicia el servicio `pqrs-backend`
- Verifica que el servicio esté funcionando

---

### 2. `deploy-frontend.sh` - Desplegar Frontend en S3

Compila el frontend Angular y lo sube a S3.

**Uso:**
```bash
./scripts/deploy-frontend.sh <BUCKET-NAME> [API-URL]
```

**Ejemplo:**
```bash
# Con API URL específica
./scripts/deploy-frontend.sh pqrs-alcaldia-frontend http://54.123.45.67:8000/api

# Sin API URL (usa la configurada en environment.prod.ts)
./scripts/deploy-frontend.sh pqrs-alcaldia-frontend
```

**Lo que hace:**
- Actualiza `environment.prod.ts` con la API URL (si se proporciona)
- Instala dependencias de npm
- Compila para producción (`ng build --configuration production`)
- Sube archivos a S3 usando `aws s3 sync`

**Requisitos:**
- AWS CLI instalado y configurado
- Credenciales de AWS con permisos para S3

---

### 3. `check-health.sh` - Verificar Estado del Sistema

Verifica que el backend y frontend estén funcionando correctamente.

**Uso:**
```bash
./scripts/check-health.sh <EC2-IP> [FRONTEND-URL]
```

**Ejemplo:**
```bash
./scripts/check-health.sh 54.123.45.67 http://pqrs-alcaldia-frontend.s3-website-us-east-1.amazonaws.com
```

**Lo que hace:**
- Verifica endpoint `/health` del backend
- Verifica accesibilidad del frontend
- Proporciona instrucciones para verificar RDS

---

## 🔧 Configuración Inicial

### 1. Instalar AWS CLI (si no está instalado)

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 2. Configurar AWS CLI

```bash
aws configure
```

Ingresa:
- **AWS Access Key ID**: Tu clave de acceso
- **AWS Secret Access Key**: Tu clave secreta
- **Default region**: us-east-1 (o tu región)
- **Default output format**: json

### 3. Verificar Configuración

```bash
aws s3 ls
```

Deberías ver la lista de tus buckets S3.

---

## 📝 Flujo de Trabajo Típico

### Despliegue Inicial

1. **Desplegar Backend:**
   ```bash
   # (Hacer esto manualmente siguiendo AWS_DEPLOYMENT_GUIDE.md)
   ```

2. **Desplegar Frontend:**
   ```bash
   ./scripts/deploy-frontend.sh pqrs-alcaldia-frontend http://54.123.45.67:8000/api
   ```

3. **Verificar:**
   ```bash
   ./scripts/check-health.sh 54.123.45.67 http://pqrs-alcaldia-frontend.s3-website-us-east-1.amazonaws.com
   ```

### Actualizar Después de Cambios

**Si modificaste el backend:**
```bash
git add .
git commit -m "Descripción de cambios"
git push origin master
./scripts/update-backend.sh 54.123.45.67 ~/Downloads/pqrs-backend-key.pem
```

**Si modificaste el frontend:**
```bash
git add .
git commit -m "Descripción de cambios"
git push origin master
./scripts/deploy-frontend.sh pqrs-alcaldia-frontend
```

---

## ⚠️ Notas Importantes

1. **Permisos de Archivo PEM**: El script automáticamente configura los permisos correctos (`chmod 400`)

2. **Git Push**: Los scripts NO hacen `git push`. Debes hacer commit y push manualmente antes de ejecutar los scripts.

3. **Variables de Entorno**: Los scripts no modifican el archivo `.env` en EC2. Si cambias variables de entorno, debes actualizarlas manualmente en el servidor.

4. **Caché de CloudFront**: Si usas CloudFront, después de desplegar el frontend ejecuta:
   ```bash
   aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
   ```

5. **Backups**: Siempre haz backup de la base de datos antes de actualizaciones importantes:
   ```bash
   # Desde EC2
   pg_dump -h RDS_ENDPOINT -U pqrsadmin pqrs_db > backup_$(date +%Y%m%d).sql
   ```

---

## 🐛 Troubleshooting

### Error: "Permission denied (publickey)"
```bash
# Verifica que el archivo PEM tenga los permisos correctos
chmod 400 ~/Downloads/pqrs-backend-key.pem

# Verifica que estás usando la IP pública correcta
```

### Error: "An error occurred (NoSuchBucket)"
```bash
# Verifica que el bucket existe
aws s3 ls s3://pqrs-alcaldia-frontend

# Verifica que tienes permisos
aws s3api get-bucket-policy --bucket pqrs-alcaldia-frontend
```

### Backend no reinicia correctamente
```bash
# Conecta a EC2 y verifica logs
ssh -i ~/Downloads/pqrs-backend-key.pem ubuntu@54.123.45.67
sudo journalctl -u pqrs-backend -n 50 --no-pager
```

---

## 📚 Referencias

- Guía completa de despliegue: `AWS_DEPLOYMENT_GUIDE.md`
- Documentación del proyecto: `README.md`

---

¡Despliegues felices! 🎉
