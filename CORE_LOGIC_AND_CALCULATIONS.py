"""
================================================================================
CORE LOGIC AND ENGINEERING CALCULATIONS
โปรแกรมคำนวณพารามิเตอร์ทางปฐพีกลศาสตร์ (Geotechnical Parameters Calculation)
================================================================================

โปรแกรมนี้ใช้สำหรับคำนวณพารามิเตอร์ทางปฐพีกลศาสตร์จากข้อมูล SPT (Standard Penetration Test)
โดยมีการคำนวณตามหลักวิศวกรรมปฐพีกลศาสตร์และมาตรฐานสากล

ข้อมูลนำเข้า (Input):
    - Depth (ความลึก, m)
    - SPT N-value (จำนวนครั้งการตอก/30 ซม., blow/ft)
    - Soil Classification (ประเภทดิน: CH, CL, SM, SC, SP-SM)
    - Ground Elevation (ระดับปากหลุม, m)
    - Water Level (ระดับน้ำ, m)

พารามิเตอร์ที่คำนวณได้ (Output):
    1. γsat - Unit Weight (น้ำหนักหน่วยของดินเปียก, kN/m³)
    2. Elevation (ระดับความสูง, m)
    3. σv' - Vertical Effective Stress (ความเค้นประสิทธิผลในแนวดิ่ง, kN/m²)
    4. CN - Correction Factor for Overburden Pressure (ค่าแก้ไขสำหรับแรงกดทับ)
    5. Ncor - Corrected N-value (ค่า N ที่แก้ไขแล้ว, blow/ft)
    6. Su - Undrained Shear Strength (กำลังรับแรงเฉือนแบบไม่ระบายน้ำ สำหรับดินเหนียว, kN/m²)
    7. Ø' - Effective Friction Angle (มุมเสียดทานประสิทธิผล สำหรับดินทราย, degrees)
    8. E/E' - Young's Modulus (โมดูลัสยืดหยุ่น, kN/m²)
    9. ν - Poisson's Ratio (อัตราส่วนปัวซงส์)
    10. K0 - Coefficient of Earth Pressure at Rest (สัมประสิทธิ์แรงดันดินขณะหยุดนิ่ง)
    11. Rint - Interface Friction (ค่าความเสียดทานระหว่างผิวสัมผัส)

================================================================================
"""

import math


# ============================================================================
# ส่วนที่ 1: ฟังก์ชันคำนวณพารามิเตอร์พื้นฐาน
# ============================================================================

def calculate_gamma_sat(n_value):
    """
    คำนวณ γsat (Unit Weight) จากค่า N

    หลักการ:
        ใช้ความสัมพันธ์เชิงประจักษ์ระหว่าง SPT N-value กับน้ำหนักหน่วยของดิน
        โดยดินที่มีค่า N สูงจะมีความหนาแน่นมากขึ้น จึงมีน้ำหนักหน่วยสูงขึ้น

    Args:
        n_value (float): SPT N-value (blow/ft)

    Returns:
        float: γsat (kN/m³)

    ตารางอ้างอิง:
        N = 0         → γsat = 0 kN/m³ (ไม่มีดิน/น้ำ)
        N < 5         → γsat = 15 kN/m³ (ดินอ่อนมาก)
        N = 5-7       → γsat = 16 kN/m³ (ดินอ่อน)
        N = 8-10      → γsat = 17 kN/m³ (ดินปานกลาง)
        N = 11-26     → γsat = 18 kN/m³ (ดินแน่น)
        N = 27-34     → γsat = 19 kN/m³ (ดินแน่นมาก)
        N ≥ 35        → γsat = 20 kN/m³ (ดินแน่นแน่น)
    """
    if n_value == 0:
        return 0
    elif n_value < 5:
        return 15
    elif n_value < 8:
        return 16
    elif n_value < 11:
        return 17
    elif n_value < 27:
        return 18
    elif n_value < 35:
        return 19
    else:
        return 20


def calculate_elevation(ground_elev, depth):
    """
    คำนวณ Elevation จาก Ground Elevation และ Depth

    หลักการ:
        Elevation = Ground Elevation - Depth
        (ระดับความสูง = ระดับปากหลุม - ความลึก)

    Args:
        ground_elev (float): ระดับปากหลุม (m MSL)
        depth (float): ความลึกจากปากหลุม (m)

    Returns:
        float: Elevation (m MSL)

    ตัวอย่าง:
        ปากหลุมอยู่ที่ระดับ +100 m MSL
        ความลึก 5 m
        → Elevation = 100 - 5 = +95 m MSL
    """
    return ground_elev - depth


def calculate_water_level(ground_elev, water_depth_from_ground):
    """
    คำนวณระดับน้ำจากระดับปากหลุมและระดับน้ำจากปากหลุม

    Args:
        ground_elev (float): ระดับปากหลุม (m)
        water_depth_from_ground (float): ระดับน้ำจากปากหลุม (m)
            - ค่าลบ (-) หมายถึงน้ำอยู่ใต้ปากหลุม
            - ค่าบวก (+) หมายถึงน้ำอยู่เหนือปากหลุม (น้ำท่วม)

    Returns:
        float: ระดับน้ำ (m)

    ตัวอย่าง:
        ปากหลุมอยู่ที่ระดับ +100 m 
        น้ำอยู่ลึกจากปากหลุม 2 m (water_depth_from_ground = -2)
        → Water Level = 100 + (-2) = +98 m
    """
    return ground_elev + water_depth_from_ground


def classify_soil(classification):
    """
    แยกประเภทดิน Sand หรือ Clay จาก USCS Classification

    หลักการ:
        ใช้ระบบ USCS (Unified Soil Classification System) ในการแบ่งประเภทดิน

    Args:
        classification (str): รหัสประเภทดินตาม USCS

    Returns:
        str: "Clay", "Sand", หรือ "" (ไม่ทราบประเภท)

    ประเภทดิน:
        Clay (ดินเหนียว):
            - CL: Clay with Low Plasticity (ดินเหนียวพลาสติกต่ำ)
            - CH: Clay with High Plasticity (ดินเหนียวพลาสติกสูง)

        Sand (ดินทราย/ดินทรายปนเหนียว):
            - SM: Silty Sand (ดินทรายปนดินตะกอน)
            - SC: Clayey Sand (ดินทรายปนดินเหนียว)
            - SP-SM: Poorly Graded Sand with Silt (ดินทรายเกรดไม่ดีปนดินตะกอน)
    """
    if classification in ["CL", "CH"]:
        return "Clay"
    elif classification in ["SM", "SC", "SP-SM"]:
        return "Sand"
    else:
        return ""


# ============================================================================
# ส่วนที่ 2: ฟังก์ชันคำนวณความเค้นและแรงดัน
# ============================================================================

def calculate_sigma_v_prime(prev_sigma, gamma_sat, depth, prev_depth, water_level, elevation):
    """
    คำนวณ Vertical Effective Stress (σv')

    หลักการ:
        σv' = Σ(γ × Δh) - u

        โดย:
        - เหนือระดับน้ำ: σv' = σv'(ก่อนหน้า) + γsat × Δh
        - ใต้ระดับน้ำ: σv' = σv'(ก่อนหน้า) + (γsat - γw) × Δh

        γw = 9.81 kN/m³ (น้ำหนักหน่วยของน้ำ)

        Effective Stress Principle (Terzaghi):
        σ' = σ - u
        โดย σ' = Effective Stress, σ = Total Stress, u = Pore Water Pressure

    Args:
        prev_sigma (float): σv' ของชั้นก่อนหน้า (kN/m²)
        gamma_sat (float): น้ำหนักหน่วยของดินเปียก (kN/m³)
        depth (float): ความลึกปัจจุบัน (m)
        prev_depth (float): ความลึกก่อนหน้า (m)
        water_level (float): ระดับน้ำ (m MSL)
        elevation (float): Elevation ปัจจุบัน (m MSL)

    Returns:
        float: σv' (kN/m²)

    ตัวอย่าง:
        ชั้นที่ 1: ความลึก 0-2 m, เหนือน้ำ, γsat = 18 kN/m³
        → σv' = 0 + 18 × 2 = 36 kN/m²

        ชั้นที่ 2: ความลึก 2-4 m, ใต้น้ำ, γsat = 18 kN/m³
        → σv' = 36 + (18 - 9.81) × 2 = 36 + 16.38 = 52.38 kN/m²
    """
    if depth == 0:
        return 0

    depth_increment = depth - prev_depth

    # ถ้าอยู่เหนือระดับน้ำ
    if elevation > water_level:
        return prev_sigma + gamma_sat * depth_increment
    else:
        # ถ้าอยู่ใต้ระดับน้ำ (ลบแรงลอยตัว)
        gamma_submerged = gamma_sat - 9.81  # γ' = γsat - γw
        return prev_sigma + gamma_submerged * depth_increment


# ============================================================================
# ส่วนที่ 3: ฟังก์ชันคำนวณค่าแก้ไข SPT N-value
# ============================================================================

def calculate_cn(sigma_v_prime, soil_type):
    """
    คำนวณ CN (Correction factor for overburden pressure)
    ใช้สำหรับดินทราย (Sand) เท่านั้น

    หลักการ:
        CN = √(100 / σv')  [σv' ในหน่วย kN/m²]

        เนื่องจากค่า SPT N-value ได้รับผลกระทบจากแรงกดทับ (Overburden Pressure)
        ดังนั้นต้องปรับแก้ค่า N ให้เป็นมาตรฐานที่ σv' = 100 kN/m²

        อ้างอิง:
        - Liao and Whitman (1986)
        - ใช้กับดินทรายเท่านั้น (ดินเหนียวไม่ต้องใช้ CN)

    Args:
        sigma_v_prime (float): Vertical effective stress (kN/m²)
        soil_type (str): "Sand" หรือ "Clay"

    Returns:
        float: CN (ไม่มีหน่วย) หรือ None (ถ้าไม่ใช่ Sand)

    ตัวอย่าง:
        σv' = 25 kN/m² → CN = √(100/25) = 2.0
        σv' = 100 kN/m² → CN = √(100/100) = 1.0
        σv' = 400 kN/m² → CN = √(100/400) = 0.5

    ข้อจำกัด:
        CN ควรอยู่ในช่วง 0.6 ≤ CN ≤ 2.0 (แต่ในโค้ดนี้ยังไม่ได้จำกัด)
    """
    if soil_type != "Sand":
        return None

    if sigma_v_prime <= 0:
        return 0

    return math.sqrt(100 / sigma_v_prime)


def calculate_ncor(n_value, cn, soil_type, correction_method="Liao and Whitman (1986)"):
    """
    คำนวณ Ncor (Corrected N-value)

    หลักการ:
        ปรับแก้ค่า N-value ให้ได้มาตรฐานเพื่อใช้ในการคำนวณต่อไป

    วิธีการ:
        1. Liao and Whitman (1986) - สำหรับดินทราย:
           Ncor = CN × N

        2. Terzaghi (1984) - สำหรับดินทราย:
           ถ้า N ≤ 15: Ncor = N
           ถ้า N > 15: Ncor = 15 + 0.5(N - 15)

        3. สำหรับดินเหนียว (Clay):
           Ncor = N (ไม่ต้องปรับแก้)

    Args:
        n_value (float): SPT N-value (blow/ft)
        cn (float): CN factor (จาก calculate_cn)
        soil_type (str): "Sand" หรือ "Clay"
        correction_method (str): "Liao and Whitman (1986)" หรือ "Terzaghi (1984)"

    Returns:
        float: Ncor (blow/ft)

    ตัวอย่าง (Liao and Whitman):
        N = 20, CN = 1.5, ดินทราย
        → Ncor = 1.5 × 20 = 30

    ตัวอย่าง (Terzaghi):
        N = 25, ดินทราย
        → Ncor = 15 + 0.5(25 - 15) = 20
    """
    if n_value is None or n_value == "":
        return None

    n_value = float(n_value)

    if soil_type == "Sand":
        if correction_method == "Liao and Whitman (1986)":
            return cn * n_value
        else:  # Terzaghi (1984)
            if n_value > 15:
                return (n_value - 15) * 0.5 + 15
            else:
                return n_value
    else:  # Clay
        return n_value


# ============================================================================
# ส่วนที่ 4: ฟังก์ชันคำนวณกำลังรับแรงเฉือนและมุมเสียดทาน
# ============================================================================

def calculate_su(ncor, classification, soil_type, su_input=None):
    """
    คำนวณ Su (Undrained Shear Strength) สำหรับดินเหนียว

    หลักการ:
        Su = α × Ncor × Pa

        โดย:
        - Pa = 9.81 kN/m² (Atmospheric pressure)
        - α = ค่าสัมประสิทธิ์ขึ้นอยู่กับประเภทดิน

        ค่า α:
        - CH (High Plasticity Clay): α = 0.6739
        - CL (Low Plasticity Clay): α = 0.5077

        อ้างอิง:
        - Stroud (1974): Su/N60 ≈ 4-6 kN/m² (เฉลี่ย 5 kN/m²)
        - Terzaghi and Peck (1967)

    Args:
        ncor (float): Corrected N-value (blow/ft)
        classification (str): ประเภทดิน (CH, CL)
        soil_type (str): "Clay" หรือ "Sand"
        su_input (float): ค่า Su จากแลป (ถ้ามี) - ไม่ใช้งานในเวอร์ชันนี้

    Returns:
        float: Su (kN/m²) หรือ None (ถ้าไม่ใช่ Clay)

    ตัวอย่าง (CH):
        Ncor = 10
        → Su = 10 × 0.6739 × 9.81 = 66.11 kN/m²

    ตัวอย่าง (CL):
        Ncor = 10
        → Su = 10 × 0.5077 × 9.81 = 49.81 kN/m²

    หมายเหตุ:
        - Su ใช้ในการวิเคราะห์ในสภาวะไม่ระบายน้ำ (Undrained condition)
        - เหมาะสำหรับการโหลดเร็ว (Quick loading)
    """
    # ถ้ามีค่าจากแลป ให้ใช้ค่านั้นแทน (ในเวอร์ชันนี้ยังไม่ implement)
    if su_input is not None and su_input != "":
        return None

    if soil_type != "Clay" or ncor is None:
        return None

    if classification == "CH":
        return ncor * 0.6739 * 9.81
    else:  # CL
        return ncor * 0.5077 * 9.81


def calculate_phi(ncor, soil_type, phi_input=None):
    """
    คำนวณ Ø' (Effective Friction Angle) สำหรับดินทราย

    หลักการ:
        Ø' = 27.1 + 0.3 × Ncor - 0.00054 × Ncor²

        สมการนี้เป็นความสัมพันธ์เชิงประจักษ์จากการทดสอบ

        อ้างอิง:
        - Peck, Hanson, and Thornburn (1974)
        - Meyerhof (1956)
        - Schmertmann (1975)

    Args:
        ncor (float): Corrected N-value (blow/ft)
        soil_type (str): "Clay" หรือ "Sand"
        phi_input (float): ค่า Ø' จากแลป (ถ้ามี)

    Returns:
        float: Ø' (degrees) หรือ None (ถ้าไม่ใช่ Sand)

    ตัวอย่าง:
        Ncor = 10
        → Ø' = 27.1 + 0.3(10) - 0.00054(10²)
        → Ø' = 27.1 + 3.0 - 0.054 = 30.05°

        Ncor = 30
        → Ø' = 27.1 + 0.3(30) - 0.00054(30²)
        → Ø' = 27.1 + 9.0 - 0.486 = 35.61°

    ข้อจำกัด:
        - สมการนี้ใช้ได้กับ Ncor ในช่วง 5-50
        - Ø' โดยทั่วไปอยู่ในช่วง 28-40° สำหรับดินทราย

    หมายเหตุ:
        - Ø' ใช้ในการวิเคราะห์ในสภาวะระบายน้ำได้ (Drained condition)
        - เหมาะสำหรับการโหลดช้า (Slow loading)
    """
    # ถ้ามีค่าจากแลป ใช้ค่านั้น
    if phi_input is not None and phi_input != "":
        return float(phi_input)

    if soil_type != "Sand" or ncor is None:
        return None

    return 27.1 + 0.3 * ncor - 0.00054 * (ncor ** 2)


# ============================================================================
# ส่วนที่ 5: ฟังก์ชันคำนวณ Modulus และ Poisson's Ratio
# ============================================================================

def calculate_e_modulus(su, ncor, soil_type, structure_type):
    """
    คำนวณ E, E' (Young's Modulus / Elastic Modulus)

    หลักการ:
        โมดูลัสยืดหยุ่นของดินขึ้นอยู่กับ:
        1. ประเภทดิน (Clay/Sand)
        2. ความแข็งแรงของดิน (Su สำหรับ Clay, Ncor สำหรับ Sand)
        3. ประเภทโครงสร้าง (ระดับความเครียดที่เกิดขึ้น)

    สำหรับดินเหนียว (Clay):
        E = α × Su

        โดยค่า α ขึ้นอยู่กับประเภทโครงสร้างและค่า Su:

        Sheet Pile (ความเครียดสูง):
            Su ≤ 2.5:    α = 150
            2.5 < Su ≤ 5: α = 300
            Su > 5:      α = 500

        Earth Retaining Structure (ความเครียดปานกลาง):
            Su ≤ 2.5:    α = 250
            2.5 < Su ≤ 5: α = 350
            Su > 5:      α = 500

        Diaphragm Wall (ความเครียดต่ำ):
            Su ≤ 2.5:    α = 500
            2.5 < Su ≤ 5: α = 750
            Su > 5:      α = 1000

    สำหรับดินทราย (Sand):
        E' = β × Ncor

        Sheet Pile: E' = 0 (ไม่นิยมใช้)
        Earth Retaining Structure: β = 1000 kN/m²
        Diaphragm Wall: β = 2000 kN/m²

    Args:
        su (float): Undrained shear strength (kN/m²)
        ncor (float): Corrected N-value
        soil_type (str): "Clay" หรือ "Sand"
        structure_type (str): "Sheet Pile", "Earth Retaining Structure", "Diaphragm Wall"

    Returns:
        float: E or E' (kN/m²)

    ตัวอย่าง (Clay - Earth Retaining):
        Su = 50 kN/m²
        → E = 50 × 500 = 25,000 kN/m²

    ตัวอย่าง (Sand - Diaphragm Wall):
        Ncor = 20
        → E' = 20 × 2000 = 40,000 kN/m²

    อ้างอิง:
        - Duncan and Buchignani (1976)
        - NAVFAC DM-7 (1982)
    """
    if soil_type == "Clay":
        if su is None or su == 0:
            return 0

        if structure_type == "Sheet Pile":
            if su <= 2.5:
                return su * 150
            elif su <= 5:
                return su * 300
            else:
                return su * 500
        elif structure_type == "Earth Retaining Structure":
            if su <= 2.5:
                return su * 250
            elif su <= 5:
                return su * 350
            else:
                return su * 500
        else:  # Diaphragm Wall
            if su <= 2.5:
                return su * 500
            elif su <= 5:
                return su * 750
            else:
                return su * 1000
    else:  # Sand
        if structure_type == "Sheet Pile":
            return 0  # ไม่นิยมใช้ Sheet Pile กับดินทราย
        elif structure_type == "Earth Retaining Structure":
            return ncor * 1000 if ncor else 0
        else:  # Diaphragm Wall
            return ncor * 2000 if ncor else 0


def calculate_poisson_ratio(soil_type):
    """
    คำนวณ ν (Poisson's Ratio / อัตราส่วนปัวซงส์)

    หลักการ:
        Poisson's Ratio คือ อัตราส่วนระหว่างความเครียดในแนวตั้งฉากต่อความเครียดในแนวแกน

        ν = -ε_lateral / ε_axial

        ค่า ν บอกว่าเมื่อวัสดุถูกกดในแนวดิ่ง จะขยายตัวในแนวนอนเท่าไร

    ค่ามาตรฐาน:
        - Clay (ดินเหนียว): ν = 0.495 (เกือบ 0.5 = incompressible)
          เนื่องจากดินเหนียวในสภาวะไม่ระบายน้ำถือว่าไม่อัดตัว

        - Sand (ดินทราย): ν = 0.333 (ประมาณ 1/3)
          ดินทรายอัดตัวได้มากกว่า

    Args:
        soil_type (str): "Clay" หรือ "Sand"

    Returns:
        float: ν (ไม่มีหน่วย)

    ช่วงค่าทั่วไป:
        - ดินเหนียวอิ่มตัวน้ำ (saturated): 0.40-0.50
        - ดินเหนียวไม่อิ่มตัว (unsaturated): 0.10-0.30
        - ดินทราย: 0.25-0.40
        - หิน: 0.15-0.25

    หมายเหตุ:
        - ค่า ν = 0.5 หมายถึงวัสดุไม่อัดตัว (incompressible)
        - ค่า ν ส่วนใหญ่อยู่ระหว่าง 0-0.5
    """
    if soil_type == "Clay":
        return 0.495
    elif soil_type == "Sand":
        return 0.333
    else:
        return 0


# ============================================================================
# ส่วนที่ 6: ฟังก์ชันคำนวณแรงดันดินและค่าเสียดทาน
# ============================================================================

def calculate_k0(soil_type, phi, structure_type):
    """
    คำนวณ K0 (Coefficient of Earth Pressure at Rest)

    หลักการ:
        K0 คือ อัตราส่วนระหว่างแรงดันดินในแนวนอนต่อแรงดันดินในแนวดิ่งในสภาวะหยุดนิ่ง

        K0 = σh' / σv'

        โดย:
        σh' = Horizontal effective stress
        σv' = Vertical effective stress

    วิธีการคำนวณ:

        สำหรับดินเหนียว (Clay):
            - Sheet Pile: K0 = 0.65
            - โครงสร้างอื่นๆ: K0 = 0.80

        สำหรับดินทราย (Sand):
            ใช้ Jaky's Formula (1944):
            K0 = 1 - sin(Ø')

            โดย Ø' = มุมเสียดทานประสิทธิผล (radians)

    Args:
        soil_type (str): "Clay" หรือ "Sand"
        phi (float): Friction angle (degrees) - ใช้กับ Sand เท่านั้น
        structure_type (str): ประเภทโครงสร้าง

    Returns:
        float: K0 (ไม่มีหน่วย)

    ตัวอย่าง (Sand):
        Ø' = 30°
        → K0 = 1 - sin(30°) = 1 - 0.5 = 0.5

        Ø' = 35°
        → K0 = 1 - sin(35°) = 1 - 0.574 = 0.426

    ช่วงค่าทั่วไป:
        - ดินทรายหลวม: K0 = 0.50-0.60
        - ดินทรายแน่น: K0 = 0.40-0.50
        - ดินเหนียว NC (Normally Consolidated): K0 = 0.50-0.70
        - ดินเหนียว OC (Over Consolidated): K0 = 0.70-2.00

    อ้างอิง:
        - Jaky (1944): K0 = 1 - sin(Ø')
        - Mayne and Kulhawy (1982): K0 = (1 - sin(Ø')) × OCR^sin(Ø')
    """
    if soil_type == "Clay":
        if structure_type == "Sheet Pile":
            return 0.65
        else:
            return 0.8
    elif soil_type == "Sand" and phi is not None:
        phi_rad = math.radians(phi)
        return 1 - math.sin(phi_rad)
    else:
        return 0


def calculate_rint(su, soil_type, method, surface_type):
    """
    คำนวณ Rint (Interface Friction / ค่าความเสียดทานระหว่างผิวสัมผัส)

    หลักการ:
        Rint = tan(δ) / tan(Ø')

        โดย:
        δ = มุมเสียดทานระหว่างดินกับวัสดุโครงสร้าง
        Ø' = มุมเสียดทานของดิน

    สำหรับดินเหนียว (Clay):
        ขึ้นอยู่กับวิธีการก่อสร้างและค่า Su

        Method = "Driven":
            Su < 2.5:        Rint = 1.00 (full adhesion)
            2.5 ≤ Su < 7.5:  Rint = 1.00 - 0.5×((Su-2.5)/5)  (linear interpolation)
            Su ≥ 7.5:        Rint = 0.50

        Method = "Bored":
            Rint = 0.45 (all cases)

    สำหรับดินทราย (Sand):
        ขึ้นอยู่กับประเภทผิวสัมผัส

        - Rough Concrete: Rint = 1.0
        - Smooth Concrete: Rint = 0.8
        - Rough Steel:    Rint = 0.7
        - Smooth Steel:   Rint = 0.5
        - Timber:         Rint = 0.8

    Args:
        su (float): Undrained shear strength (kN/m²)
        soil_type (str): "Clay" or "Sand"
        method (str): "Driven" or "Bored"
        surface_type (str): "Rough Concrete", "Smooth Concrete", "Rough Steel",
                           "Smooth Steel", "Timber"

    Returns:
        float: Rint (ไม่มีหน่วย, 0-1)

    ตัวอย่าง (Clay - ตอก/กด):
        Su = 50 kN/m² (> 7.5)
        → Rint = 0.50

        Su = 5 kN/m² (2.5-7.5)
        → Rint = 1.00 - 0.5×((5-2.5)/5) = 1.00 - 0.25 = 0.75

    ตัวอย่าง (Sand - คอนกรีตผิวเรียบ):
        → Rint = 0.8

    อ้างอิง:
        - API RP 2A (2000)
        - NAVFAC DM-7.2 (1982)
        - Tomlinson (1957) - สำหรับ adhesion factor
    """
    if soil_type == "Clay":
        if method == "Driven":
            if su is None or su == 0:
                return 0
            if su < 2.5:
                return 1
            elif su < 7.5:
                return 1 - (0.5 * ((su - 2.5) / 5))
            else:
                return 0.5
        else:  # Bored
            return 0.45
    else:  # Sand
        surface_map = {
            "Rough Concrete": 1.0,
            "Smooth Concrete": 0.8,
            "Rough Steel": 0.7,
            "Smooth Steel": 0.5,
            "Timber": 0.8
        }
        return surface_map.get(surface_type, 0)


# ============================================================================
# ส่วนที่ 7: ฟังก์ชันหลักสำหรับคำนวณพารามิเตอร์ทั้งหมด
# ============================================================================

def calculate_all_parameters(borehole_data, settings):
    """
    ฟังก์ชันหลักสำหรับคำนวณพารามิเตอร์ทางปฐพีกลศาสตร์ทั้งหมด

    หลักการทำงาน:
        1. รับข้อมูลหลุมเจาะและการตั้งค่า
        2. Loop คำนวณทีละชั้นดิน
        3. คำนวณพารามิเตอร์ตามลำดับ (เนื่องจากบางค่าต้องใช้ค่าจากชั้นก่อนหน้า)
        4. เก็บผลลัพธ์ในรูปแบบ list of dictionaries

    Args:
        borehole_data (dict): ข้อมูลหลุมเจาะ
            {
                'name': str,                    # ชื่อหลุมเจาะ (เช่น "BH-1")
                'ground_elevation': float,      # ระดับปากหลุม (m MSL)
                'water_depth': float,           # ระดับน้ำจากปากหลุม (m, ลบ = ใต้ปากหลุม)
                'data': [                       # ข้อมูลแต่ละชั้น
                    {
                        'depth': float,         # ความลึก (m)
                        'spt': float,           # SPT N-value (blow/ft)
                        'classification': str   # ประเภทดิน (CH, CL, SM, SC, SP-SM)
                    },
                    ...
                ]
            }

        settings (dict): การตั้งค่าสำหรับการคำนวณ
            {
                'structure_type': str,          # "Sheet Pile", "Earth Retaining Structure",
                                               # "Diaphragm Wall"
                'method': str,                  # "Driven", "Bored"
                'surface_type': str,            # "Rough Concrete", "Smooth Concrete",
                                               # "Rough Steel", "Smooth Steel", "Timber"
                'correction_method': str        # "Liao and Whitman (1986)", "Terzaghi (1984)"
            }

    Returns:
        list: รายการผลลัพธ์แต่ละชั้นดิน
            [
                {
                    'depth': float,             # ความลึก (m)
                    'elevation': float,         # ระดับความสูง (m MSL)
                    'gamma_sat': float,         # น้ำหนักหน่วย (kN/m³)
                    'classification': str,      # ประเภทดิน (CH, CL, SM, SC, SP-SM)
                    'soil_type': str,           # "Clay" หรือ "Sand"
                    'n_value': float,           # SPT N-value (blow/ft)
                    'sigma_v': float,           # σv' (kN/m²)
                    'cn': float,                # CN (สำหรับ Sand)
                    'ncor': float,              # Ncor (blow/ft)
                    'su': float,                # Su (kN/m²) สำหรับ Clay
                    'phi': float,               # Ø' (degrees) สำหรับ Sand
                    'e_modulus': float,         # E, E' (kN/m²)
                    'poisson': float,           # ν
                    'k0': float,                # K0
                    'rint': float               # Rint
                },
                ...
            ]

    ขั้นตอนการคำนวณ (สำหรับแต่ละชั้น):

        1. คำนวณพารามิเตอร์พื้นฐาน:
           - Elevation = Ground Elevation - Depth
           - Soil Type = classify_soil(Classification)
           - γsat = calculate_gamma_sat(N)

        2. คำนวณความเค้น:
           - σv' = calculate_sigma_v_prime(...)
             ขึ้นอยู่กับ σv' ของชั้นก่อนหน้า, γsat, ความลึก, และระดับน้ำ

        3. คำนวณค่าแก้ไข N-value (สำหรับ Sand):
           - CN = calculate_cn(σv', soil_type)
           - Ncor = calculate_ncor(N, CN, soil_type, correction_method)

        4. คำนวณกำลังรับแรงเฉือนและมุมเสียดทาน:
           - Su = calculate_su(Ncor, classification, soil_type)  [Clay only]
           - Ø' = calculate_phi(Ncor, soil_type)                [Sand only]

        5. คำนวณพารามิเตอร์ความยืดหยุ่น:
           - E/E' = calculate_e_modulus(Su, Ncor, soil_type, structure_type)
           - ν = calculate_poisson_ratio(soil_type)

        6. คำนวณแรงดันดินและค่าเสียดทาน:
           - K0 = calculate_k0(soil_type, Ø', structure_type)
           - Rint = calculate_rint(Su, soil_type, method, surface_type)

        7. บันทึกผลลัพธ์และไปชั้นถัดไป

    ตัวอย่างการใช้งาน:
        >>> borehole_data = {
        ...     'name': 'BH-1',
        ...     'ground_elevation': 100.0,
        ...     'water_depth': -2.0,
        ...     'data': [
        ...         {'depth': 1.0, 'spt': 5, 'classification': 'CL'},
        ...         {'depth': 2.0, 'spt': 10, 'classification': 'CH'},
        ...         {'depth': 3.0, 'spt': 15, 'classification': 'SM'}
        ...     ]
        ... }
        >>> settings = {
        ...     'structure_type': 'Earth Retaining Structure',
        ...     'method': 'Driven',
        ...     'surface_type': 'Smooth Concrete',
        ...     'correction_method': 'Liao and Whitman (1986)'
        ... }
        >>> results = calculate_all_parameters(borehole_data, settings)
        >>> print(f"Calculated {len(results)} layers")

    หมายเหตุ:
        - การคำนวณต้องทำตามลำดับ เพราะ σv' ของแต่ละชั้นต้องใช้ค่าจากชั้นก่อนหน้า
        - สำหรับดินเหนียว จะคำนวณเฉพาะ Su (ไม่มี Ø')
        - สำหรับดินทราย จะคำนวณเฉพาะ Ø' (ไม่มี Su)
    """
    ground_elev = borehole_data['ground_elevation']
    water_level = calculate_water_level(ground_elev, borehole_data['water_depth'])

    results = []
    prev_sigma = 0      # σv' เริ่มต้น = 0 ที่ผิวดิน
    prev_depth = 0      # ความลึกเริ่มต้น = 0

    # Loop คำนวณทีละชั้นดิน
    for point in borehole_data['data']:
        depth = point['depth']
        n_value = point['spt']
        classification = point['classification']

        # ขั้นตอนที่ 1: คำนวณพารามิเตอร์พื้นฐาน
        elevation = calculate_elevation(ground_elev, depth)
        soil_type = classify_soil(classification)
        gamma_sat = calculate_gamma_sat(n_value) if n_value else 0

        # ขั้นตอนที่ 2: คำนวณ σv' (ใช้ค่าจากชั้นก่อนหน้า)
        sigma_v = calculate_sigma_v_prime(
            prev_sigma, gamma_sat, depth, prev_depth, water_level, elevation
        )

        # ขั้นตอนที่ 3: คำนวณ CN และ Ncor (สำหรับ Sand)
        cn = calculate_cn(sigma_v, soil_type)
        ncor = calculate_ncor(n_value, cn, soil_type, settings['correction_method'])

        # ขั้นตอนที่ 4: คำนวณ Su และ Ø'
        su = calculate_su(ncor, classification, soil_type)
        phi = calculate_phi(ncor, soil_type)

        # ขั้นตอนที่ 5: คำนวณพารามิเตอร์ความยืดหยุ่น
        e_modulus = calculate_e_modulus(su, ncor, soil_type, settings['structure_type'])
        poisson = calculate_poisson_ratio(soil_type)

        # ขั้นตอนที่ 6: คำนวณแรงดันดินและค่าเสียดทาน
        k0 = calculate_k0(soil_type, phi, settings['structure_type'])
        rint = calculate_rint(su, soil_type, settings['method'], settings['surface_type'])

        # เก็บผลลัพธ์
        results.append({
            'depth': depth,
            'elevation': elevation,
            'gamma_sat': gamma_sat,
            'classification': classification,
            'soil_type': soil_type,
            'n_value': n_value,
            'sigma_v': sigma_v,
            'cn': cn,
            'ncor': ncor,
            'su': su,
            'phi': phi,
            'e_modulus': e_modulus,
            'poisson': poisson,
            'k0': k0,
            'rint': rint
        })

        # อัพเดทค่าสำหรับชั้นถัดไป
        prev_sigma = sigma_v
        prev_depth = depth

    return results


# ============================================================================
# ส่วนที่ 8: ตัวอย่างการใช้งาน (Demo)
# ============================================================================

if __name__ == "__main__":
    """
    ตัวอย่างการใช้งานฟังก์ชันคำนวณ
    รันไฟล์นี้โดยตรงเพื่อทดสอบการคำนวณ
    """

    print("="*100)
    print("GEOTECHNICAL PARAMETERS CALCULATION - DEMONSTRATION")
    print("="*100)

    # ตัวอย่างข้อมูลหลุมเจาะ
    sample_borehole = {
        'name': 'BH-1',
        'ground_elevation': 99.054,
        'water_depth': -0.70,
        'data': [
            {'depth': 1.45, 'spt': 8, 'classification': 'CH'},
            {'depth': 2.45, 'spt': 12, 'classification': 'CL'},
            {'depth': 3.45, 'spt': 15, 'classification': 'SM'},
            {'depth': 4.95, 'spt': 20, 'classification': 'SC'},
            {'depth': 6.45, 'spt': 25, 'classification': 'SM'},
        ]
    }

    # ตัวอย่างการตั้งค่า
    sample_settings = {
        'structure_type': 'Earth Retaining Structure',
        'method': 'Driven',
        'surface_type': 'Smooth Concrete',
        'correction_method': 'Liao and Whitman (1986)'
    }

    # แสดงข้อมูลนำเข้า
    print(f"\nBorehole Information:")
    print(f"  Name: {sample_borehole['name']}")
    print(f"  Ground Elevation: {sample_borehole['ground_elevation']} m MSL")
    print(f"  Water Depth from Ground: {sample_borehole['water_depth']} m")
    water_level = calculate_water_level(
        sample_borehole['ground_elevation'],
        sample_borehole['water_depth']
    )
    print(f"  Water Level: {water_level:.2f} m MSL")

    print(f"\nCalculation Settings:")
    print(f"  Structure Type: {sample_settings['structure_type']}")
    print(f"  Construction Method: {sample_settings['method']}")
    print(f"  Surface Type: {sample_settings['surface_type']}")
    print(f"  SPT Correction Method: {sample_settings['correction_method']}")

    # คำนวณพารามิเตอร์ทั้งหมด
    print("\n" + "="*100)
    print("CALCULATION RESULTS")
    print("="*100)

    results = calculate_all_parameters(sample_borehole, sample_settings)

    # แสดงผลลัพธ์ในรูปแบบตาราง
    sigma_v_label = "σv'"
    phi_label = "Ø'"
    e_label = "E/E'"
    header = (
        f"{'Depth':<8} {'Elev':<8} {'γsat':<8} {'Class':<6} {'Type':<6} "
        f"{'N':<6} {sigma_v_label:<10} {'CN':<8} {'Ncor':<8} "
        f"{'Su':<10} {phi_label:<8} {e_label:<12} {'ν':<8} {'K0':<8} {'Rint':<8}"
    )
    print(f"\n{header}")
    print("-"*130)

    for r in results:
        # Format ค่าต่างๆ
        depth = f"{r['depth']:.2f}"
        elev = f"{r['elevation']:.2f}"
        gamma = f"{r['gamma_sat']:.1f}" if r['gamma_sat'] else "-"
        class_ = r['classification']
        soil_type = r['soil_type']
        n = f"{r['n_value']:.0f}" if r['n_value'] else "-"
        sigma = f"{r['sigma_v']:.2f}" if r['sigma_v'] else "-"
        cn = f"{r['cn']:.3f}" if r['cn'] else "-"
        ncor = f"{r['ncor']:.2f}" if r['ncor'] else "-"
        su = f"{r['su']:.2f}" if r['su'] else "-"
        phi = f"{r['phi']:.2f}" if r['phi'] else "-"
        e = f"{r['e_modulus']:.0f}" if r['e_modulus'] else "-"
        nu = f"{r['poisson']:.3f}" if r['poisson'] else "-"
        k0 = f"{r['k0']:.3f}" if r['k0'] else "-"
        rint = f"{r['rint']:.2f}" if r['rint'] else "-"

        print(
            f"{depth:<8} {elev:<8} {gamma:<8} {class_:<6} {soil_type:<6} "
            f"{n:<6} {sigma:<10} {cn:<8} {ncor:<8} "
            f"{su:<10} {phi:<8} {e:<12} {nu:<8} {k0:<8} {rint:<8}"
        )

    print("\n" + "="*100)
    print("END OF CALCULATION")
    print("="*100)
