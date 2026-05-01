# ClearUnit

- **Project:** Flask property management system
- **Stack:** Python 3.11, Flask, PostgreSQL, SQLAlchemy, Flask-Migrate, Flask-Login, Werkzeug, Jinja2, Tailwind CDN
- **DB:** postgresql://localhost/clearunit_db
- **Models:** User, Building, Unit, Dues, Payment, Announcement, MaintenanceRequest
- **Roles:** manager (owns multiple buildings), resident (one unit)
- **Structure:** app/routes (auth, manager, resident), app/templates, config.py, run.py
- **Rules:** be concise, no explanations, make changes directly, all queries scoped by building_id
