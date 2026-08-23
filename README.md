# Sistema de Monitoreo y Predicción de Calidad de Composta

Proyecto modular — Ingeniería Informática (INNI).
Monitoreo IoT (simulado) + predicción de calidad con Random Forest.

## Estructura

```
composta-system/
├── database/            # Scripts SQL (schema + seed)
│   ├── schema.sql
│   └── seed.sql
├── backend/             # API REST FastAPI
│   ├── app/
│   │   ├── main.py      # App FastAPI (+ handler Mangum para Lambda)
│   │   ├── config.py    # Configuración vía .env
│   │   ├── database.py  # Conexión SQLAlchemy → MySQL
│   │   ├── core/        # Seguridad (JWT, hashing)
│   │   ├── models/      # Modelos SQLAlchemy (tablas)
│   │   ├── schemas/     # Esquemas Pydantic (request/response)
│   │   └── routers/     # Endpoints: auth, lotes, predicciones
│   ├── scripts/
│   │   └── crear_admin.py
│   ├── requirements.txt
│   └── .env.example
├── ml/                  # Machine Learning
│   ├── generar_dataset.py   (pendiente — módulo ML)
│   ├── entrenar_modelo.py   (pendiente — módulo ML)
│   └── modelos/             # modelo_composta.joblib (generado)
├── simulador/           # Simulador de sensor
│   └── simulador_local.py   (pendiente — HTTP local; luego MQTT/IoT Core)
└── frontend/            # React + CoreUI (ver instrucciones abajo)
```

## Rangos óptimos de composta

| Parámetro   | Rango óptimo |
|-------------|--------------|
| Temperatura | 45–65 °C     |
| Humedad     | 40–60 %      |
| pH          | 6–8          |

## Setup local

### 1. Base de datos (MySQL local)

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # editar credenciales MySQL
python scripts/crear_admin.py   # crea usuario admin
uvicorn app.main:app --reload --port 8000
```

Docs interactivas: http://localhost:8000/docs

### 3. Frontend (CoreUI React)

```bash
git clone https://github.com/coreui/coreui-free-react-admin-template.git frontend
cd frontend
npm install
npm install axios recharts
npm start
```

## Migración a AWS (futuro)

| Local              | AWS                          |
|--------------------|------------------------------|
| FastAPI (uvicorn)  | Lambda + API Gateway (Mangum ya incluido) |
| MySQL local        | RDS MySQL (solo cambia DATABASE_URL en .env) |
| Simulador HTTP     | Simulador MQTT → IoT Core → Lambda |
| React (npm start)  | S3 + CloudFront              |

## Endpoints

- `POST /auth/login`
- `GET /lotes` · `POST /lotes`
- `GET /lotes/{id}/registros`
- `GET /lotes/{id}/predicciones`
- `POST /predicciones/{id_lote}`
