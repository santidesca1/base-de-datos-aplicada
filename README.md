# HEFESTO — Energía Renovable MEM (Dashboard online)

App de Streamlit con 5 pestañas: Paso 1 a Paso 4 de la metodología HEFESTO
(documentación real de la entrega) y, al final, el Dashboard interactivo con
las 9 preguntas de negocio.

La base de datos (`energia.db`) ya viene cargada y commiteada al repositorio
— es SQLite, un único archivo, así que la app **no necesita ningún servidor
de base de datos aparte** para funcionar en Render. `build_sqlite.py` +
`schema_sqlite.sql` + `base_de_datos.csv` quedan en el repo solo como
evidencia de cómo se generó (Paso 4), no hace falta correrlos para desplegar.

## Cómo subir esto a GitHub (sin usar la terminal)

1. Entrá a [github.com/new](https://github.com/new) con tu cuenta.
2. Nombre del repositorio: por ejemplo `hefesto-energia-renovable`. Dejalo
   en **Public** (Render free necesita que el repo sea público, o que
   conectes tu cuenta de GitHub a Render para repos privados). Creá el
   repositorio vacío (sin README, sin .gitignore).
3. En la página del repo recién creado, click en **"uploading an existing
   file"** (o el botón Add file → Upload files).
4. Arrastrá **todos** los archivos de esta carpeta (los que están al mismo
   nivel que este README, no la carpeta en sí) y confirmá el commit.

## Cómo desplegar en Render

1. Entrá a [render.com](https://render.com) y creá tu cuenta con **"Sign up
   with GitHub"** (así queda conectado directo, sin pasos extra).
2. Dashboard de Render → **New** → **Web Service**.
3. Elegí **"Build and deploy from a Git repository"** y seleccioná el repo
   que acabás de subir (`hefesto-energia-renovable`).
4. Render va a detectar el `render.yaml` solo y completar:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - **Plan:** Free
   Si no lo autocompleta, pegalos vos a mano con esos mismos valores.
5. Click en **Create Web Service**. El primer build tarda 2-5 minutos
   (instala las librerías de Python). Cuando termine, Render te da una URL
   del estilo `https://hefesto-energia-renovable.onrender.com`.

## Después de desplegar

- El plan free de Render "duerme" el servicio después de ~15 minutos sin
  tráfico, y la primera visita después de eso tarda ~30-50 segundos en
  despertar. Para la presentación: abrí la URL un par de minutos antes de
  empezar, así ya está despierta cuando la muestres en vivo.
- Si en algún momento querés actualizar el contenido (texto, gráficos,
  estilo), basta con subir los archivos nuevos al mismo repo de GitHub
  (reemplazando los viejos) — Render redespliega solo cada vez que detecta
  un cambio en el repo.
