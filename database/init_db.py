import datetime
import logging
from database.db_connection import engine, Base, SessionLocal
from database.models import Shelter, Hospital, Alert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("disaster_assist.init_db")

def init_database():
    """Generates the SQLite database schema and seeds base mock resources."""
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if database is already seeded
        if db.query(Shelter).first() is not None:
            logger.info("Database already seeded with shelters. Skipping seed phase.")
            return

        logger.info("Seeding base shelters...")
        shelters = [
            Shelter(
                name="Civic Center Gymnasium",
                latitude=37.774929,
                longitude=-122.419416,
                capacity=150,
                occupancy=42,
                status="OPEN",
                address="99 Grove St, San Francisco, CA 94102",
                contact_info="Emergency Shelter Line: (415) 554-6000"
            ),
            Shelter(
                name="Golden Gate Park Pavilion",
                latitude=37.769421,
                longitude=-122.486214,
                capacity=300,
                occupancy=290,
                status="OPEN",
                address="501 Stanyan St, San Francisco, CA 94117",
                contact_info="Park Ranger Station: (415) 831-2700"
            ),
            Shelter(
                name="Mission High School Auditorium",
                latitude=37.761891,
                longitude=-122.427218,
                capacity=200,
                occupancy=200,
                status="FULL",
                address="3750 18th St, San Francisco, CA 94114",
                contact_info="Red Cross Disaster: (800) 733-2767"
            )
        ]
        db.add_all(shelters)
        
        logger.info("Seeding base hospitals...")
        hospitals = [
            Hospital(
                name="Zuckerberg San Francisco General Hospital",
                latitude=37.755431,
                longitude=-122.404832,
                status="OPERATIONAL",
                emergency_services=True,
                contact_info="Emergency Department: (415) 206-8000"
            ),
            Hospital(
                name="UCSF Medical Center at Mission Bay",
                latitude=37.767812,
                longitude=-122.391211,
                status="OPERATIONAL",
                emergency_services=True,
                contact_info="General Line: (415) 353-3000"
            ),
            Hospital(
                name="Saint Francis Memorial Hospital",
                latitude=37.789121,
                longitude=-122.415132,
                status="OVERLOADED",
                emergency_services=True,
                contact_info="Reception: (415) 353-6000"
            )
        ]
        db.add_all(hospitals)
        
        logger.info("Seeding initial alerts...")
        alerts = [
            Alert(
                title="Tsunami Watch - Coastal SF Bay",
                description="A tsunami watch has been issued for the coastal regions of the San Francisco Bay Area following an offshore magnitude 7.2 earthquake. Evacuate low-lying areas if directed.",
                severity="WATCH",
                latitude=37.7749,
                longitude=-122.4194,
                radius_km=25.0,
                expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=6)
            )
        ]
        db.add_all(alerts)
        
        db.commit()
        logger.info("Database initialization and seed operations completed successfully.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {str(e)}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
