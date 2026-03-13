# 🔐 Configuración de Google Drive para JurisBot

## Problema Detectado

El token de OAuth actual tiene scope `readonly` para Google Drive. Necesitas autorizar el scope de escritura para crear carpetas y subir archivos.

---

## Solución: Autorizar Scope de Drive

### **Paso 1: Generar URL de Autorización**

Abre esta URL en tu navegador:

```
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=TU_CLIENT_ID_AQUI
  &redirect_uri=http://localhost:8085
  &response_type=code
  &scope=https://www.googleapis.com/auth/drive.file
  &access_type=offline
  &prompt=consent
```

**URL completa (copiar y pegar):**
```
https://accounts.google.com/o/oauth2/v2/auth?client_id=TU_CLIENT_ID_AQUI&redirect_uri=http://localhost:8085&response_type=code&scope=https://www.googleapis.com/auth/drive.file&access_type=offline&prompt=consent
```

---

### **Paso 2: Obtener Código de Autorización**

1. Abre la URL en tu navegador
2. Inicia sesión con tu cuenta de Google (ivanjose@gmail.com)
3. Acepta los permisos para Google Drive
4. Serás redirigido a `localhost:8085` (dará error, es normal)
5. **Copia el código de la URL** (parámetro `code=...`)

---

### **Paso 3: Intercambiar Código por Token**

```bash
curl -X POST https://oauth2.googleapis.com/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "code=COPIA_EL_CODIGO_AQUI" \
  -d "client_id=TU_CLIENT_ID_AQUI" \
  -d "client_secret=TU_CLIENT_SECRET_AQUI" \
  -d "redirect_uri=http://localhost:8085" \
  -d "grant_type=authorization_code"
```

---

### **Paso 4: Actualizar .env**

El resultado te dará un nuevo `refresh_token`. Actualiza el archivo:

```bash
# /root/.nanobot/workspace/.env
GOOGLE_REFRESH_TOKEN=nuevo_refresh_token_aqui
```

---

## Alternativa Temporal

Mientras configuras los permisos, puedo:

1. **Crear un ZIP** con todos los archivos de JurisBot
2. **Subirlo a un servicio temporal** (transfer.sh)
3. **Enviarte el enlace** para que lo descargues manualmente

¿Prefieres configurar los permisos de Drive o usar la alternativa temporal?