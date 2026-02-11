# ============================================================
# PLAXIS 2024.1 - Create Multiple Soil Materials (Mohr-Coulomb)
# ============================================================

from plxscripting.easy import *
import os

# ------------------------------------------------------------
# Connect to PLAXIS
# ------------------------------------------------------------
password = os.getenv("PLAXIS_PASSWORD")
s_i, g_i = new_server('localhost', 10000, password=password)
print("Connected to PLAXIS")


# ------------------------------------------------------------
# Soil database
# ------------------------------------------------------------




soil_data = [
    {
        "name": "01 Sand, Medium Dense",
        "gammaUnsat": 15.5,
        "gammaSat": 16.5,
        "Eref": 13000,
        "nu": 0.30,
        "cRef": 0.0,
        "phi": 32.0,
        "GroundwaterClassificationType": 2,
        "GroundwaterSoilClassUSDA": 0, # Sand
        "Rinter": 0.8
    },
    {
        "name": "02 Clay, Soft",
        "gammaUnsat": 14.0,
        "gammaSat": 16.0,
        "Eref": 5000,
        "nu": 0.35,
        "cRef": 10.0,
        "phi": 22.0,
        "GroundwaterClassificationType": 2,
        "GroundwaterSoilClassUSDA": 11,# Clay
        "Rinter": 0.7
    },
    {
        "name": "03 Sand, Dense",
        "gammaUnsat": 17.0,
        "gammaSat": 19.0,
        "Eref": 30000,
        "nu": 0.28,
        "cRef": 0.0,
        "phi": 38.0,
        "GroundwaterClassificationType": 2,
        "GroundwaterSoilClassUSDA": 0, # Sand
        "Rinter": 0.9
    }
]

# ------------------------------------------------------------
# Create materials in loop
# ------------------------------------------------------------
for data in soil_data:

    soil = g_i.soilmat()

    # General
    soil.Identification = data["name"]
    soil.SoilModel = "Mohr-Coulomb"
    soil.DrainageType = "Drained"

    # Unit weights
    soil.gammaUnsat = data["gammaUnsat"]
    soil.gammaSat = data["gammaSat"]

    # Mechanical - Stiffness
    soil.ERef = data["Eref"]
    soil.nu = data["nu"]

    # Mechanical - Strength
    soil.cRef = data["cRef"]
    soil.phi = data["phi"]

    # Groundwater
    soil.GroundwaterClassificationType  = data["GroundwaterClassificationType"]
    soil.GroundwaterSoilClassUSDA = data["GroundwaterSoilClassUSDA"]

    soil.GwUseDefaults = True
    soil.GwDefaultsMethod = 1


    # Interfaces
    soil.InterfaceStrengthDetermination = 1   # Manual
    soil.Rinter = data["Rinter"]

    # Initial - K0
    soil.K0Determination = 0

    print(f"Created material: {data['name']}")

print("==============================================")
print("All soil materials created successfully")
print("==============================================")
