from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import os
import secrets

# Tiedosto, johon PostgreSQL-salasana tallennetaan, jotta se pysyy samana eri käynnistysten välillä
password_file = "/app/management_password.txt"

# Jos salasana on jo tallennettu tiedostoon, käytetään sitä
if os.path.exists(password_file):
    with open(password_file, "r") as f:
        db_password = f.read().strip()
else:
    # Käytetään ympäristömuuttujaa, jos se on saatavilla, muuten generoidaan uusi salasana
    db_password = os.getenv("POSTGRES_PASSWORD", secrets.token_urlsafe(16))

    # Tallennetaan salasana tiedostoon, jotta se pysyy samana palvelun uudelleenkäynnistyksessä
    with open(password_file, "w") as f:
        f.write(db_password)

# Rakennetaan tietokantayhteyden osoite
DATABASE_URL = f"postgresql://management_user:{db_password}@db:5432/management"

# SQLAlchemy asetukset
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

metadata = MetaData()
