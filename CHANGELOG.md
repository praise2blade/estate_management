# 📜 Estate Visitor Management System – Changelog

All notable changes to this project will be documented in this file.

## [v1.1.0] - 2025-04-18

### ✨ Added
- Resident unique code generation in format: `SERA-R-0001`, `SERA-R-0002`, etc.
- Landlord unique code generation in format: `SERA-L-0001`, `SERA-L-0002`, etc.
- Dependent management feature:
  - Created `Dependent` model linked to `Resident`
  - Auto-generate dependent codes in format: `SERA-R-0001-C1`, `SERA-R-0001-W`, etc.
  - Form for adding Dependents with dependent type dropdown.
  - List view for Dependents.

### 🛠️ Fixed
- AttributeError in `add_dependent` view corrected by replacing `request.user.resident` with `request.user.resident_profile`
- Corrected Dependent type dropdown rendering using Django `choices`.
- Fixed unique code generation for Dependents to properly attach to Resident’s code.

### 🗄️ Database
- Dropped previous database.
- Re-created migrations.
- Applied fresh migrations.
- Created new superuser.

**Commands run:**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
