import math
import statistics
import sys

def print_header(text):
    print(f"\n{'='*60}\n{text}\n{'='*60}")

def check_exit(user_input):
    """Checks if the user wants to terminate the program."""
    if user_input.lower() in ['exit', 'q', 'quit']:
        print("\nExiting program. Analysis terminated by user.")
        sys.exit()

def get_float_input(prompt):
    """Helper function to ensure user enters a valid number or exit command."""
    while True:
        raw_val = input(prompt).strip()
        check_exit(raw_val)
        try:
            return float(raw_val)
        except ValueError:
            print("Invalid input! Please enter a numerical value or type 'exit' to quit.")

def run_za_uncertainty_analysis():
    print_header("TOTAL NITROGEN CONTENT IN ZA FERTILIZER MEASUREMENT UNCERTAINTY EVALUATOR\nBased on Rusli et al. 2026, An Interactive Python Script-Based Approach...")
    
    # NEW: Initial User Guidance Prompt
    print("USER GUIDANCE & FEATURES:")
    print(" 1. Input Data: Enter numbers as prompted.")
    print(" 2. Replicates: In Step 1, enter all %N values separated by a space.")
    print(" 3. Exit Feature: Type 'exit' or 'q' at any prompt to close the program.")
    print(" 4. Robustness: Script handles typos without crashing.")
    print("-" * 60)

    # STEP 1: Experimental Repeatability (Type A Evaluation - Section 3.4)
    print("\n[STEP 1] REPEATABILITY (Section 3.4)")
    while True:
        raw_input = input("Enter %N results from your replicates (separated by space) or 'exit': ").strip()
        check_exit(raw_input)
        try:
            n_results = [float(x) for x in raw_input.split()]
            if len(n_results) < 2:
                print("Error: Please enter at least 2 measurements to calculate repeatability.")
                continue
            
            mean_n = statistics.mean(n_results)
            std_dev = statistics.stdev(n_results) # Eq. 5
            u_rel_rep = std_dev / mean_n           # Eq. 6
            n_count = len(n_results)
            
            print(f"-> Detected n = {n_count} replicates.")
            print(f"-> Mean Nitrogen: {mean_n:.4f}% | Standard Deviation (s): {std_dev:.4f}")
            break
        except ValueError:
            print("Invalid input! Use numbers separated by spaces (e.g., 21.02 21.05).")

    # STEP 2: Volumetric Uncertainty (Burette - Section 3.5)
    print("\n[STEP 2] VOLUMETRIC UNCERTAINTY (Section 3.5)")
    v_nom = get_float_input("Burette Nominal Volume (mL) [e.g. 25]: ")
    tol_b = get_float_input("Manufacturer Tolerance (mL) [±, e.g. 0.06]: ")
    u_cal = tol_b / math.sqrt(3) # Eq. 7 (Rectangular Distribution)
    
    temp_var = get_float_input("Lab Temperature Variation (°C) [±, e.g. 5]: ")
    alpha = get_float_input("Volumetric Expansion Coefficient (°C^-1) [e.g. 2.1e-4]: ")
    u_temp = (v_nom * temp_var * alpha) / math.sqrt(3) # Eq. 8
    
    u_v_burette = math.sqrt(u_cal**2 + u_temp**2) # Eq. 9 (Combined Burette)
    u_rel_v_burette = u_v_burette / v_nom
    print(f"-> Combined u(V): {u_v_burette:.6f} mL | Rel. u(V): {u_rel_v_burette:.6f}")

    # STEP 3: Mass Uncertainty (Analytical Balance - Section 3.7)
    print("\n[STEP 3] MASS UNCERTAINTY (Section 3.7)")
    u_bal_cert = get_float_input("Balance Expanded Uncertainty (mg) [e.g. 0.8]: ")
    k_bal = get_float_input("Balance Coverage Factor (k) [e.g. 1.96]: ") # 95% confidence level
    u_m_g = (u_bal_cert / k_bal) / 1000 # Eq. 11 (Convert mg to g)
    
    m_sample = get_float_input("Average ZA Sample Mass (g) [e.g. 0.50398]: ")
    m_ox = get_float_input("Average Oxalic Acid Mass (g) [e.g. 0.3247]: ")
    u_rel_ms = u_m_g / m_sample
    u_rel_mox = u_m_g / m_ox

    # STEP 4: Purity & Constants (Section 3.6, 3.8, 3.9)
    print("\n[STEP 4] PURITY & CONSTANTS (Section 3.6)")
    p_cert = get_float_input("Oxalic Acid Purity (fraction) [e.g. if the oxalic acid purity is 99.95%, please input as 0.9995]: ")
    p_tol = get_float_input("Purity Tolerance (±) [e.g. if the oxalic acid purity is 99.95%, the purity tolerance can be calculated as 100%-99.95% = 0.05%, hence the purity tolerance is 0.0005, then please input as 0.0005]: ")
    u_p = p_tol / math.sqrt(6) # Eq. 10 (Triangular Distribution)
    u_rel_p = u_p / p_cert
    
    u_rel_m_molar = 0.000019 # From Section 3.8 calculation (see Table 4)
    u_rel_ar_n = 0.000005    # From Section 3.9 calculation (see Table 4)

    # STEP 5: Final Combination (Section 3.10)
    # Combining relative uncertainties in quadrature per Eq. 14 and Eq. 16
    # Note: u_rel_v is included twice (sample titration and standardization)
    u_rel_model = math.sqrt(
        (u_rel_v_burette**2) + (u_rel_v_burette**2) + 
        (u_rel_ms**2) + (u_rel_mox**2) + 
        (u_rel_p**2) + (u_rel_m_molar**2) + (u_rel_ar_n**2)
    )
    
    u_rel_total = math.sqrt((u_rel_model**2) + (u_rel_rep**2)) # Eq. 16
    u_absolute = u_rel_total * mean_n # Eq. 17
    expanded_u = u_absolute * 2      # Eq. 18 (k=2)

    # FINAL REPORT
    print_header("FINAL UNCERTAINTY BUDGET SUMMARY")
    print(f"1. Number of Replicates (n): {n_count}")
    print(f"2. Reported Mean Nitrogen: {mean_n:.4f} %")
    print(f"3. Combined Standard Uncertainty (u_c): ± {u_absolute:.4f} %")
    print(f"4. Expanded Uncertainty (U): ± {expanded_u:.4f} %")
    print(f"5. Coverage Factor: k = 2 (95% Confidence)")
    print(f"\nFinal Analytical Result: ({mean_n:.3f} ± {expanded_u:.3f}) % N")
    print("="*60)

if __name__ == "__main__":
    try:
        run_za_uncertainty_analysis()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by keyboard. Closing.")
        sys.exit()
