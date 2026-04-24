#!/usr/bin/env python
import math
import statistics
import sys


def print_header(text):
    print(f"\n{'='*78}\n{text}\n{'='*78}")


def check_exit(user_input):
    """Exit safely if user types exit/q/quit."""
    if user_input.lower() in ["exit", "q", "quit"]:
        print("\nExiting program. Analysis terminated by user.")
        sys.exit()


def get_float_input(prompt, default=None):
    """Read a float with optional default."""
    while True:
        raw_val = input(prompt).strip()
        check_exit(raw_val)

        if raw_val == "" and default is not None:
            return float(default)

        try:
            return float(raw_val)
        except ValueError:
            print("Invalid input! Please enter a numerical value or type 'exit' to quit.")


def get_int_input(prompt, default=None):
    """Read an integer with optional default."""
    while True:
        raw_val = input(prompt).strip()
        check_exit(raw_val)

        if raw_val == "" and default is not None:
            return int(default)

        try:
            return int(raw_val)
        except ValueError:
            print("Invalid input! Please enter an integer or type 'exit' to quit.")


def get_float_list(prompt, min_len=1):
    """Read a list of floats separated by spaces."""
    while True:
        raw_val = input(prompt).strip()
        check_exit(raw_val)

        try:
            values = [float(x) for x in raw_val.split()]
            if len(values) < min_len:
                print(f"Please enter at least {min_len} value(s).")
                continue
            return values
        except ValueError:
            print("Invalid input! Use numbers separated by spaces.")


def round_value_with_uncertainty(value, uncertainty, sig_figs_unc=2):
    """
    Round uncertainty to 1-2 significant figures and round the value
    to the same decimal place.
    """
    if uncertainty <= 0:
        return str(value), str(uncertainty)

    exponent = math.floor(math.log10(abs(uncertainty)))
    decimals = sig_figs_unc - 1 - exponent

    rounded_u = round(uncertainty, decimals)
    rounded_value = round(value, decimals)

    fmt = f"{{:.{max(decimals, 0)}f}}"
    return fmt.format(rounded_value), fmt.format(rounded_u)


def segment_count(actual_volume_ml, burette_capacity_ml):
    return max(1, math.ceil(actual_volume_ml / burette_capacity_ml))


def burette_uncertainty_per_segment(
    burette_capacity_ml,
    tolerance_ml,
    temp_variation_c,
    alpha,
    smallest_division_ml
):
    u_read_single = (smallest_division_ml / 2.0) / math.sqrt(3.0)
    u_read_segment = math.sqrt(2.0) * u_read_single
    u_cal_segment = tolerance_ml / math.sqrt(3.0)
    u_temp_segment = (burette_capacity_ml * temp_variation_c * alpha) / math.sqrt(3.0)

    u_segment = math.sqrt(
        u_read_segment ** 2 +
        u_cal_segment ** 2 +
        u_temp_segment ** 2
    )

    return {
        "u_read_single": u_read_single,
        "u_read_segment": u_read_segment,
        "u_cal_segment": u_cal_segment,
        "u_temp_segment": u_temp_segment,
        "u_segment": u_segment,
    }


def total_delivered_volume_uncertainty(actual_volume_ml, burette_capacity_ml, u_segment_ml):
    n_seg = segment_count(actual_volume_ml, burette_capacity_ml)
    return math.sqrt(n_seg) * u_segment_ml


def compute_model_relative_uncertainty(
    v_sample_ml,
    v_std_ml,
    m_sample_g,
    m_ox_g,
    purity_fraction,
    u_purity_abs,
    m_ox_molar_g_mol,
    u_m_ox_molar_abs,
    a_n_g_mol,
    u_a_n_abs,
    burette_capacity_ml,
    u_segment_ml,
    u_mass_g
):
    u_v_sample = total_delivered_volume_uncertainty(v_sample_ml, burette_capacity_ml, u_segment_ml)
    u_v_std = total_delivered_volume_uncertainty(v_std_ml, burette_capacity_ml, u_segment_ml)

    ur_v_sample = u_v_sample / v_sample_ml
    ur_v_std = u_v_std / v_std_ml
    ur_purity = u_purity_abs / purity_fraction
    ur_m_ox = u_mass_g / m_ox_g
    ur_m_sample = u_mass_g / m_sample_g
    ur_m_ox_molar = u_m_ox_molar_abs / m_ox_molar_g_mol
    ur_a_n = u_a_n_abs / a_n_g_mol

    rel_components = {
        "Burette volume reading for sample": ur_v_sample,
        "Burette volume reading for standardization": ur_v_std,
        "Oxalic acid purity": ur_purity,
        "Oxalic acid mass measurement": ur_m_ox,
        "ZA sample mass measurement": ur_m_sample,
        "Oxalic acid molar mass": ur_m_ox_molar,
        "Nitrogen atomic mass": ur_a_n,
    }

    abs_components = {
        "Burette volume reading for sample": u_v_sample,
        "Burette volume reading for standardization": u_v_std,
        "Oxalic acid purity": u_purity_abs,
        "Oxalic acid mass measurement": u_mass_g,
        "ZA sample mass measurement": u_mass_g,
        "Oxalic acid molar mass": u_m_ox_molar_abs,
        "Nitrogen atomic mass": u_a_n_abs,
    }

    segment_info = {
        "sample_segments": segment_count(v_sample_ml, burette_capacity_ml),
        "std_segments": segment_count(v_std_ml, burette_capacity_ml),
    }

    ur_model = math.sqrt(sum(v ** 2 for v in rel_components.values()))
    return ur_model, rel_components, abs_components, segment_info


def contribution_percent(ur_component, ur_total):
    if ur_total == 0:
        return 0.0
    return (ur_component ** 2 / ur_total ** 2) * 100.0


def print_uncertainty_budget_table(title, rows):
    print_header(title)
    print(
        f"{'Input quantity of uncertainty':45s}"
        f"{'Value':>12s}"
        f"{'u(xi)':>14s}"
        f"{'Unit':>12s}"
        f"{'ur(xi)':>12s}"
    )
    print("-" * 105)
    for name, value, ux, unit, ur in rows:
        print(f"{name:45s}{value:12.6f}{ux:14.6f}{unit:12s}{ur:12.6f}")


def run_za_uncertainty_analysis():
    print_header(
        "TOTAL NITROGEN CONTENT IN ZA FERTILIZER MEASUREMENT UNCERTAINTY EVALUATOR\n"
        "Based on Rusli, et al., 2026. An Interactive Python Script-Based Approach..., ACS Omega"
    )

    print("USER GUIDANCE & FEATURES:")
    print(" 1. Input Data: Enter the value as requested.")
    print(" 2. Robustness: Script handles typos without crashing.")
    print(" 3. Type 'exit' or 'q' at any prompt to quit.")
    print(" 4. Press Enter to use default values.")
    print(" 5. The results might be slightly different from manual calculation due to rounding.")
    print("-" * 78)

    # ==========================================================
    # STEP 1: NaOH STANDARDIZATION + ZA TITRATION + REPEATABILITY
    # ==========================================================
    print_header("STEP 1. NaOH STANDARDIZATION, ZA TITRATION, AND REPEATABILITY")

    # ---------- PART A: NaOH standardization ----------
    print("\n[PART A] NaOH STANDARDIZATION")
    print("\nWe assumed the use of oxalic acid dihydrate as standard, therefore the molar mass is 126.064 g/mol")
    n_std = get_int_input("How many replicate standardizations of NaOH were performed? ")

    std_masses = []
    std_volumes = []
    naoh_concentrations = []

    MOLAR_MASS_OXALIC = 126.064

    print("\nEnter the oxalic acid mass (g) example: 0.3214 and NaOH volume used (mL) example: 20.5 for each standardization replicate.")
    print("NaOH concentration is calculated as:")
    print("M_NaOH = (2 × m_oxalic) / (M_oxalic × V_NaOH in L)\n")

    for i in range(1, n_std + 1):
        print(f"Standardization replicate {i}:")
        m_ox = get_float_input("  Oxalic acid mass (g): ")
        v_naoh_ml = get_float_input("  NaOH volume used (mL): ")

        v_naoh_l = v_naoh_ml / 1000.0
        m_naoh = (2.0 * m_ox) / (MOLAR_MASS_OXALIC * v_naoh_l)

        std_masses.append(m_ox)
        std_volumes.append(v_naoh_ml)
        naoh_concentrations.append(m_naoh)

    avg_naoh = statistics.mean(naoh_concentrations)
    avg_naoh = round(avg_naoh, 4)
    sd_naoh = statistics.stdev(naoh_concentrations) if len(naoh_concentrations) > 1 else 0.0
    cv_naoh = (sd_naoh / avg_naoh) * 100 if avg_naoh != 0 else 0.0

    print_header("NaOH STANDARDIZATION RESULTS")
    print(f"{'Replicate':<12}{'Oxalic acid (g)':<20}{'NaOH volume (mL)':<22}{'NaOH concentration (M)':<24}")
    print("-" * 78)
    for i, (m_ox, v_naoh_ml, m_naoh) in enumerate(zip(std_masses, std_volumes, naoh_concentrations), start=1):
        print(f"{i:<12}{m_ox:<20.4f}{v_naoh_ml:<22.1f}{m_naoh:<24.4f}")

    print("-" * 78)
    print(f"Average NaOH concentration (M): {avg_naoh:.4f}")
    print(f"Standard deviation (M):         {sd_naoh:.4f}")
    print(f"Coefficient of variation (%):  {cv_naoh:.4f}")

    # Select representative NaOH standardization replicate
    rep_std_index = get_int_input(
        f"\nWhich NaOH standardization replicate should be used for the representative uncertainty budget? "
        f"(1 to {n_std}) [default = 1]: ",
        default=1
    )

    if rep_std_index < 1 or rep_std_index > n_std:
        print("Representative standardization index out of range. Using replicate 1.")
        rep_std_index = 1

    rep_std_m_ox = std_masses[rep_std_index - 1]
    rep_std_v_naoh = std_volumes[rep_std_index - 1]
    rep_std_m_naoh = naoh_concentrations[rep_std_index - 1]

    print(f"\nRepresentative NaOH standardization replicate selected: #{rep_std_index}")
    print(f"-> Oxalic acid mass: {rep_std_m_ox:.6f} g")
    print(f"-> NaOH volume: {rep_std_v_naoh:.6f} mL")
    print(f"-> NaOH concentration from this replicate: {rep_std_m_naoh:.6f} M")
    print("Note: The average NaOH concentration is used for final %N calculation,")
    print("      while this selected replicate is used only for the representative uncertainty budget.")

    # ---------- PART B: ZA titration for nitrogen determination ----------
    print("\n[PART B] ZA FERTILIZER TITRATION FOR NITROGEN DETERMINATION")
    print("\nWe assumed the use of atomic mass of nitrogen of 14.007 g/mol")
    n_count = get_int_input("How many ZA formol titration replicates were performed? ")

    za_masses = []
    za_volumes = []
    n_results = []

    ATOMIC_MASS_N = 14.007

    print("\nEnter the ZA sample mass (g) example: 0.5036 and NaOH volume consumed (mL) example: 30.8 for each replicate.")
    print("Nitrogen percentage is calculated as:")
    print("%N = (M_NaOH × V_NaOH(L) × Ar(N) × 100) / m_sample\n")

    for i in range(1, n_count + 1):
        print(f"ZA titration replicate {i}:")
        m_sample = get_float_input("  ZA sample mass (g): ")
        v_naoh_ml = get_float_input("  NaOH volume consumed (mL): ")

        v_naoh_l = v_naoh_ml / 1000.0
        percent_n = (avg_naoh * v_naoh_l * ATOMIC_MASS_N * 100.0) / m_sample

        za_masses.append(m_sample)
        za_volumes.append(v_naoh_ml)
        n_results.append(percent_n)

    mean_n = statistics.mean(n_results)
    mean_n = round(mean_n, 3)
    std_dev = statistics.stdev(n_results) if len(n_results) > 1 else 0.0
    std_dev = round(std_dev, 6)
    cv_n = (std_dev / mean_n) * 100 if mean_n != 0 else 0.0
    u_rel_rep = std_dev / mean_n if mean_n != 0 else 0.0
    u_rel_rep = round(u_rel_rep, 6)

    print_header("ZA TITRATION RESULTS FOR NITROGEN DETERMINATION")
    print(f"{'Replicate':<12}{'ZA mass (g)':<18}{'NaOH volume (mL)':<22}{'%N':<16}")
    print("-" * 70)
    for i, (m_sample, v_naoh_ml, percent_n) in enumerate(zip(za_masses, za_volumes, n_results), start=1):
        print(f"{i:<12}{m_sample:<18.4f}{v_naoh_ml:<22.1f}{percent_n:<16.3f}")

    print("-" * 70)
    print(f"Average %N:                    {mean_n:.3f}")
    print(f"Standard deviation (s):        {std_dev:.6f}")
    print(f"Coefficient of variation (%):  {cv_n:.3f}")
    print(f"Relative repeatability uncertainty, ur,rep = s/mean: {u_rel_rep:.6f}")

    # Select representative ZA formol titration replicate
    rep_index = get_int_input(
        f"\nWhich ZA formol titration replicate should be used for the representative uncertainty budget? "
        f"(1 to {n_count}) [default = 1]: ",
        default=1
    )

    if rep_index < 1 or rep_index > n_count:
        print("Representative ZA titration index out of range. Using replicate 1.")
        rep_index = 1

    rep_n = n_results[rep_index - 1]
    rep_sample_mass = za_masses[rep_index - 1]
    rep_sample_volume = za_volumes[rep_index - 1]

    print(f"\nRepresentative ZA formol titration replicate selected: #{rep_index}")
    print(f"-> ZA sample mass: {rep_sample_mass:.6f} g")
    print(f"-> NaOH volume consumed: {rep_sample_volume:.6f} mL")
    print(f"-> Calculated %N from this replicate: {rep_n:.6f}")

    # ==========================================================
    # STEP 2: BURETTE UNCERTAINTY
    # ==========================================================
    print_header("STEP 2. BURETTE UNCERTAINTY")
    burette_capacity_ml = get_float_input("Burette nominal capacity (mL) [example:25]: ", default=25.0)
    smallest_division_ml = get_float_input("Smallest burette division (mL) [example:0.1]: ", default=0.1)
    tolerance_ml = get_float_input("Manufacturer tolerance ± (mL) [example:0.06]: ", default=0.06)
    temp_variation_c = get_float_input("Laboratory temperature variation ± (°C) [example:5]: ", default=5.0)
    alpha = get_float_input("Volumetric expansion coefficient, alpha (°C^-1) [example:2.1e-4]: ", default=2.1e-4)

    burette_dict = burette_uncertainty_per_segment(
        burette_capacity_ml=burette_capacity_ml,
        tolerance_ml=tolerance_ml,
        temp_variation_c=temp_variation_c,
        alpha=alpha,
        smallest_division_ml=smallest_division_ml
    )

    u_segment_ml = burette_dict["u_segment"]

    print(f"-> Single meniscus reading uncertainty, u(R): {burette_dict['u_read_single']:.6f} mL")
    print(f"-> Reading uncertainty per delivered segment: {burette_dict['u_read_segment']:.6f} mL")
    print(f"-> Calibration uncertainty per segment: {burette_dict['u_cal_segment']:.6f} mL")
    print(f"-> Temperature uncertainty per segment: {burette_dict['u_temp_segment']:.6f} mL")
    print(f"-> Combined uncertainty per delivered segment: {u_segment_ml:.6f} mL")

    # ==========================================================
    # STEP 3: MASS UNCERTAINTY
    # ==========================================================
    print_header("STEP 3. MASS UNCERTAINTY")
    print("Use balance calibration certificate values where possible.")
    u_bal_expanded_mg = get_float_input("Balance expanded uncertainty, U (mg) [ex: 0.2]: ", default=0.2)
    k_bal = get_float_input("Coverage factor k from certificate [ex: 2]: ", default=2.0)

    u_mass_g = (u_bal_expanded_mg / k_bal) / 1000.0
    print(f"-> Standard uncertainty of mass measurement: {u_mass_g:.8f} g")

    # ==========================================================
    # STEP 4: PURITY & CONSTANTS
    # ==========================================================
    print_header("STEP 4. PURITY & CONSTANTS")
    purity_fraction = get_float_input("Oxalic acid purity as fraction [ex: 0.9995]: ", default=0.9995)
    purity_tol = get_float_input("Purity tolerance ± as fraction [ex: 0.0005]: ", default=0.0005)
    u_purity_abs = purity_tol / math.sqrt(6.0)

    print("\nAtomic-weight uncertainty inputs for oxalic acid dihydrate molar mass")
    m_ox_molar_g_mol = get_float_input("Oxalic acid dihydrate molar mass (g/mol) [ex: 126.064, default=126.064]: ", default=126.064)
    u_C = get_float_input("Standard uncertainty of carbon atomic mass, u_C [default: 0.002]: ", default=0.002)
    u_H = get_float_input("Standard uncertainty of hydrogen atomic mass, u_H [default: 0.0002]: ", default=0.0002)
    u_O = get_float_input("Standard uncertainty of oxygen atomic mass, u_O [default: 0.001]: ", default=0.001)
    
    u_m_ox_molar_abs = math.sqrt((2*u_C)**2 + (6*u_H)**2 + (6*u_O)**2)
    a_n_g_mol = get_float_input("Atomic mass of nitrogen (g/mol) [ex: 14.007, default=14.007]: ", default=14.007)
    u_a_n_abs = get_float_input(
        "Standard uncertainty of nitrogen atomic mass (g/mol) [ex: 0.001, default=0.001]: ",
        default=0.001
    )

    # ==========================================================
    # STEP 5: REPRESENTATIVE STANDARDIZATION INPUTS
    # ==========================================================
    print_header("STEP 5. REPRESENTATIVE STANDARDIZATION INPUTS")
    v_std_ml = rep_std_v_naoh
    m_ox_g = rep_std_m_ox

    print(f"Using representative NaOH standardization replicate #{rep_std_index}:")
    print(f"-> Standardization NaOH volume: {v_std_ml:.6f} mL")
    print(f"-> Oxalic acid mass: {m_ox_g:.6f} g")

    # ==========================================================
    # STEP 6: REPRESENTATIVE SAMPLE TITRATION INPUTS
    # ==========================================================
    print_header("STEP 6. REPRESENTATIVE SAMPLE TITRATION INPUTS")
    v_sample_rep_ml = rep_sample_volume
    m_sample_rep_g = rep_sample_mass

    print(f"Using representative ZA formol titration replicate #{rep_index}:")
    print(f"-> Sample titration NaOH volume: {v_sample_rep_ml:.6f} mL")
    print(f"-> ZA sample mass: {m_sample_rep_g:.6f} g")

    rep_ur_model, rep_rel_components, rep_abs_components, rep_segment_info = compute_model_relative_uncertainty(
        v_sample_ml=v_sample_rep_ml,
        v_std_ml=v_std_ml,
        m_sample_g=m_sample_rep_g,
        m_ox_g=m_ox_g,
        purity_fraction=purity_fraction,
        u_purity_abs=u_purity_abs,
        m_ox_molar_g_mol=m_ox_molar_g_mol,
        u_m_ox_molar_abs=u_m_ox_molar_abs,
        a_n_g_mol=a_n_g_mol,
        u_a_n_abs=u_a_n_abs,
        burette_capacity_ml=burette_capacity_ml,
        u_segment_ml=u_segment_ml,
        u_mass_g=u_mass_g
    )

    rep_rows = [
        ("Burette volume reading for sample",
         v_sample_rep_ml, rep_abs_components["Burette volume reading for sample"], "mL",
         rep_rel_components["Burette volume reading for sample"]),
        ("Burette volume reading for standardization",
         v_std_ml, rep_abs_components["Burette volume reading for standardization"], "mL",
         rep_rel_components["Burette volume reading for standardization"]),
        ("Oxalic acid purity",
         purity_fraction, rep_abs_components["Oxalic acid purity"], "fraction",
         rep_rel_components["Oxalic acid purity"]),
        ("Oxalic acid mass measurement",
         m_ox_g, rep_abs_components["Oxalic acid mass measurement"], "g",
         rep_rel_components["Oxalic acid mass measurement"]),
        ("ZA sample mass measurement",
         m_sample_rep_g, rep_abs_components["ZA sample mass measurement"], "g",
         rep_rel_components["ZA sample mass measurement"]),
        ("Oxalic acid molar mass",
         m_ox_molar_g_mol, rep_abs_components["Oxalic acid molar mass"], "g/mol",
         rep_rel_components["Oxalic acid molar mass"]),
        ("Nitrogen atomic mass",
         a_n_g_mol, rep_abs_components["Nitrogen atomic mass"], "g/mol",
         rep_rel_components["Nitrogen atomic mass"]),
    ]

    print_uncertainty_budget_table(
        f"REPRESENTATIVE UNCERTAINTY BUDGET "
        f"(Standardization Replicate #{rep_std_index}, ZA Titration Replicate #{rep_index})",
        rep_rows
    )
    print(f"\n-> Representative sample titration used {rep_segment_info['sample_segments']} filling(s).")
    print(f"-> Representative standardization used {rep_segment_info['std_segments']} filling(s).")
    print(f"-> Representative model-based relative uncertainty: {rep_ur_model:.6f}")

    # ==========================================================
    # STEP 7: MODEL-BASED UNCERTAINTY FOR ALL REPLICATES
    # ==========================================================
    print_header("STEP 7. MODEL-BASED UNCERTAINTY FOR ALL REPLICATES")
    print("Using ZA titration volumes and sample masses already entered in Step 1.")

    all_v_sample = za_volumes
    all_m_sample = za_masses

    all_ur_model = []
    for vs, ms in zip(all_v_sample, all_m_sample):
        ur_model_i, _, _, _ = compute_model_relative_uncertainty(
            v_sample_ml=vs,
            v_std_ml=v_std_ml,
            m_sample_g=ms,
            m_ox_g=m_ox_g,
            purity_fraction=purity_fraction,
            u_purity_abs=u_purity_abs,
            m_ox_molar_g_mol=m_ox_molar_g_mol,
            u_m_ox_molar_abs=u_m_ox_molar_abs,
            a_n_g_mol=a_n_g_mol,
            u_a_n_abs=u_a_n_abs,
            burette_capacity_ml=burette_capacity_ml,
            u_segment_ml=u_segment_ml,
            u_mass_g=u_mass_g
        )
        all_ur_model.append(ur_model_i)

    avg_ur_model = statistics.mean(all_ur_model)
    sd_ur_model = statistics.stdev(all_ur_model) if len(all_ur_model) > 1 else 0.0

    print(f"-> Average model-based relative uncertainty across all replicates: {avg_ur_model:.6f}")
    print(f"-> SD of model-based relative uncertainty across replicates: {sd_ur_model:.6f}")

    # ==========================================================
    # STEP 8: FINAL COMBINATION
    # ==========================================================
    print_header("STEP 8. FINAL COMBINATION")
    u_rel_total = math.sqrt(avg_ur_model ** 2 + u_rel_rep ** 2)
    u_absolute = mean_n * u_rel_total
    expanded_u = 2.0 * u_absolute
    print(f"Average relative model uncertainty, ur,model(avg): {avg_ur_model:.6f}")
    print(f"Relative repeatability uncertainty, ur,rep: {u_rel_rep:.6f}")
    print(f"Combined relative standard uncertainty, ur,total: {u_rel_total:.6f}")
    print(f"Combined absolute standard uncertainty, u_c: ± {u_absolute:.6f} %")
    print(f"Expanded uncertainty, U (k = 2): ± {expanded_u:.6f} %")

    # ==========================================================
    # STEP 9: CONTRIBUTION ANALYSIS
    # ==========================================================
    print_header("STEP 9. CONTRIBUTION ANALYSIS")
    print(f"{'Input quantity of uncertainty':45s}{'ur(xi)':>12s}{'% Contribution':>16s}")
    print("-" * 78)

    for name, ur_val in rep_rel_components.items():
        pct = contribution_percent(ur_val, u_rel_total)
        print(f"{name:45s}{ur_val:12.6f}{pct:16.3f}")

    pct_rep = contribution_percent(u_rel_rep, u_rel_total)
    print(f"{'Repeatability':45s}{u_rel_rep:12.6f}{pct_rep:16.3f}")

    # ==========================================================
    # FINAL REPORT
    # ==========================================================
    print_header("FINAL UNCERTAINTY BUDGET SUMMARY")
    print(f"1. Number of Replicates (n): {n_count}")
    print(f"2. Reported Mean Nitrogen: {mean_n:.6f} %")
    print(f"3. Relative Repeatability Uncertainty, ur,rep: {u_rel_rep:.6f}")
    print(f"4. Average Relative Model Uncertainty, ur,model(avg): {avg_ur_model:.6f}")
    print(f"5. Combined Relative Standard Uncertainty, ur,total: {u_rel_total:.6f}")
    print(f"6. Combined Standard Uncertainty, u_c: ± {u_absolute:.6f} %")
    print(f"7. Expanded Uncertainty, U (k = 2): ± {expanded_u:.6f} %")

    rounded_value, rounded_unc = round_value_with_uncertainty(mean_n, expanded_u, sig_figs_unc=2)
    print(f"\nFinal Analytical Result (rounded): {rounded_value} ± {rounded_unc} % N")
    print("=" * 78)

    print("\nNOTES:")
    print(" - The results might be slightly different from manual calculation due to rounding.")
    print(" - The representative uncertainty budget uses the selected standardization and ZA titration replicates.")
    print(" - The average NaOH concentration is used for final %N calculation.")
    print(" - The same model-based uncertainty calculation is applied to all ZA titration replicates.")
    print(" - The average relative model uncertainty is combined with repeatability uncertainty.")
    print(" - The final absolute uncertainty is expressed using the mean nitrogen value of the replicate series.")


if __name__ == "__main__":
    try:
        run_za_uncertainty_analysis()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by keyboard. Closing.")
        sys.exit()
