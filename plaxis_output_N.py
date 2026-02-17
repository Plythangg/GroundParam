from plxscripting.easy import *
import os

try:
    # --------------------------------------------------
    # 1. CONNECTION
    # --------------------------------------------------
    password = os.getenv("PLAXIS_PASSWORD")
    s_o, g_o = new_server("localhost", 10001, password=password)
    print(">>> เชื่อมต่อ PLAXIS Output สำเร็จ!")

    # --------------------------------------------------
    # 2. SETUP
    # --------------------------------------------------
    output_dir = r"C:\Users\Public\Documents\PLAXIS_Exports"
    os.makedirs(output_dir, exist_ok=True)
    img_w, img_h = 1600, 900

    # --------------------------------------------------
    # 3. GET PHASES
    # --------------------------------------------------
    phase_loading = None
    phase_lwl = None
    phase_rdd = None

    for p in g_o.Phases:
        ident = str(p.Identification)
        if "Loading" in ident:
            phase_loading = p
        elif "LWL_FS" in ident:
            phase_lwl = p
        elif "RDD_FS" in ident:
            phase_rdd = p

    print(f"Phase Loading: {phase_loading.Identification}")
    print(f"Phase LWL_FS: {phase_lwl.Identification}")
    print(f"Phase RDD_FS: {phase_rdd.Identification}")

    # --------------------------------------------------
    # 4. GET ELEMENTS
    # --------------------------------------------------
    capbeam = g_o.Plates[0]

    pile_a = None
    pile_b = None
    pile_d = []

    for eb in g_o.EmbeddedBeams:
        name = str(eb.Name)
        if "6" in name:
            pile_a = eb
        elif "7" in name:
            pile_b = eb
        else:
            pile_d.append(eb)

    print(f"\nCapBeam: {capbeam.Name}")
    print(f"Pile A: {pile_a.Name if pile_a else 'Not found'}")
    print(f"Pile B: {pile_b.Name if pile_b else 'Not found'}")
    print(f"Pile D: {len(pile_d)} elements")

    # --------------------------------------------------
    # 5. HELPER FUNCTION
    # --------------------------------------------------
    def export_plot(plot, filename):
        filepath = os.path.join(output_dir, f"{filename}.png")
        try:
            plot.export(filepath, img_w, img_h)
            print(f"  ✓ {filename}.png")
            return True
        except Exception as e:
            print(f"  ✗ {filename}: {e}")
            return False

    # ==================================================
    # PHASE: Loading
    # ==================================================
    print("\n" + "="*50)
    print("PHASE: Loading")
    print("="*50)

    # --- CapBeam ---
    print("\n[CapBeam]")
    try:
        plate_plot = g_o.structureplot(capbeam)
        plate_plot.Phase = phase_loading
        
        plate_plot.ResultType = g_o.ResultTypes.Plate.M2D
        export_plot(plate_plot, "Loading_CapBeam_M")
        
        plate_plot.ResultType = g_o.ResultTypes.Plate.Q2D
        export_plot(plate_plot, "Loading_CapBeam_Q")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # --- Pile A ---
    print("\n[Pile A]")
    try:
        pile_a_plot = g_o.structureplot(pile_a)
        pile_a_plot.Phase = phase_loading
        
        pile_a_plot.ResultType = g_o.ResultTypes.EmbeddedBeam.M2D
        export_plot(pile_a_plot, "Loading_PileA_M")
        
        pile_a_plot.ResultType = g_o.ResultTypes.EmbeddedBeam.Q2D
        export_plot(pile_a_plot, "Loading_PileA_Q")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # --- Pile B ---
    print("\n[Pile B]")
    try:
        pile_b_plot = g_o.structureplot(pile_b)
        pile_b_plot.Phase = phase_loading
        
        pile_b_plot.ResultType = g_o.ResultTypes.EmbeddedBeam.M2D
        export_plot(pile_b_plot, "Loading_PileB_M")
        
        pile_b_plot.ResultType = g_o.ResultTypes.EmbeddedBeam.Q2D
        export_plot(pile_b_plot, "Loading_PileB_Q")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # --- Pile D ---
    print("\n[Pile D]")
    try:
        if len(pile_d) > 0:
            pile_d_plot = g_o.structureplot(pile_d[0])
            pile_d_plot.Phase = phase_loading
            
            pile_d_plot.ResultType = g_o.ResultTypes.EmbeddedBeam.M2D
            export_plot(pile_d_plot, "Loading_PileD_M")
            
            pile_d_plot.ResultType = g_o.ResultTypes.EmbeddedBeam.Q2D
            export_plot(pile_d_plot, "Loading_PileD_Q")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # ==================================================
    # PHASE: LWL_FS
    # ==================================================
    print("\n" + "="*50)
    print("PHASE: LWL_FS")
    print("="*50)

    soil_plot = g_o.Plots[0]

    print("\n[Deformations & Strain]")
    try:
        soil_plot.Phase = phase_lwl
        
        soil_plot.ResultType = g_o.ResultTypes.Soil.Utot
        export_plot(soil_plot, "LWL_FS_Utot")
        
        soil_plot.ResultType = g_o.ResultTypes.Soil.TotalDeviatoricStrain
        export_plot(soil_plot, "LWL_FS_TotalStrain")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # ==================================================
    # PHASE: RDD_FS
    # ==================================================
    print("\n" + "="*50)
    print("PHASE: RDD_FS")
    print("="*50)

    print("\n[Deformations & Strain]")
    try:
        soil_plot.Phase = phase_rdd
        
        soil_plot.ResultType = g_o.ResultTypes.Soil.Utot
        export_plot(soil_plot, "RDD_FS_Utot")
        
        soil_plot.ResultType = g_o.ResultTypes.Soil.TotalDeviatoricStrain
        export_plot(soil_plot, "RDD_FS_TotalStrain")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # ==================================================
    # SUMMARY
    # ==================================================
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Output folder: {output_dir}")

    png_files = [f for f in sorted(os.listdir(output_dir)) if f.endswith('.png')]
    print(f"\nTotal PNG files: {len(png_files)}")

    for f in png_files:
        if f.startswith(("Loading_", "LWL_FS_", "RDD_FS_")):
            size = os.path.getsize(os.path.join(output_dir, f))
            print(f"  ✓ {f} ({size:,} bytes)")

except Exception as e:
    print(f"\n!!! ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
input("กด Enter เพื่อปิดหน้าต่าง...")