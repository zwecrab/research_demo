import streamlit as st
import pandas as pd
import json
import os
import sys

# Add parent directory to path since app.py is now in 'app/' folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend modules
from experiments_db import init_db, add_experiment_result, get_all_experiments, clear_all_experiments
from batch_experiment import run_single_experiment
from compare.evaluate_bias import generate_evaluation_report
from data_loader import load_all_assets

# PANAS EMOTION LISTS
POSITIVE_EMOTIONS = ["Interested", "Excited", "Strong", "Enthusiastic", "Proud", "Alert", "Inspired", "Determined", "Attentive", "Active"]
NEGATIVE_EMOTIONS = ["Distressed", "Upset", "Guilty", "Scared", "Hostile", "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"]

def calculate_panas_shift(json_path, patient_key):
    """Calculate Positive, Negative, and Net PANAS shift from a JSON transcript file."""
    try:
        if not os.path.exists(json_path):
            return 0, 0, 0
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        deltas = data.get(f"{patient_key}_PANAS_DELTA", [])
        if not deltas:
            return 0, 0, 0
            
        pos_change = sum([d.get("difference", 0) for d in deltas if d.get("feeling", "").title() in POSITIVE_EMOTIONS])
        neg_change = sum([d.get("difference", 0) for d in deltas if d.get("feeling", "").title() in NEGATIVE_EMOTIONS])
        net_change = pos_change - neg_change
        
        return pos_change, neg_change, net_change
    except Exception as e:
        return 0, 0, 0

def get_structure_from_file(json_path):
    """Extract conversation structure from JSON file."""
    try:
        if not os.path.exists(json_path):
            return "Unknown"
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("conversation_structure", "Unknown")
    except:
        return "Unknown"

def get_alliance_scores(json_path):
    """Extract therapeutic alliance scores from JSON file."""
    try:
        if not os.path.exists(json_path):
            return 0.0, 0.0, 0.0, 0.0
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ta_data = data.get("therapist_alliance", {})
        validation = ta_data.get("validation", 0.0)
        neutrality = ta_data.get("neutrality", 0.0)
        guidance = ta_data.get("guidance", 0.0)
        overall = ta_data.get("overall", 0.0)
        return validation, neutrality, guidance, overall
    except:
        return 0.0, 0.0, 0.0, 0.0


def get_balance_scores(json_path):
    """
    Extract FAS, BRD, and CAS therapeutic balance scores from a JSON transcript.

    FAS (Framing Adoption Score): -1.0 to +1.0
        Positive = therapist adopts Patient A's framing; negative = Patient B's.
    BRD (Bid Responsiveness Differential): unbounded, typically -3 to +3
        Positive = more depth toward Patient B; negative = more toward Patient A.
    CAS (Challenge Asymmetry Score): integer
        Positive = more challenges to Patient A; negative = more to Patient B.

    Returns (fas, brd, cas) or (None, None, None) if data is absent.
    """
    try:
        if not os.path.exists(json_path):
            return None, None, None
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        balance = data.get("therapeutic_balance", {})
        fas = balance.get("fas", {}).get("fas_score", None)
        brd = balance.get("brd", {}).get("brd_score", None)
        cas = balance.get("cas", {}).get("cas_score", None)
        return fas, brd, cas
    except:
        return None, None, None


# Page Config
st.set_page_config(
    page_title="AI Therapy Experiment Dashboard",
    page_icon="🧠",
    layout="wide"
)

# Initialize DB
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# Load Assets (Cached)
@st.cache_resource
def get_assets():
    return load_all_assets()

try:
    assets = get_assets()
    # Ensure topics are available
    if "therapy_plans" not in assets:
        st.error("Failed to load therapy plans from assets.")
        st.stop()
    topics = list(assets["therapy_plans"].keys())
except Exception as e:
    st.error(f"Error loading assets: {e}")
    st.stop()


# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Run Experiment", "Compare Transcripts", "Results Dashboard"])

st.sidebar.markdown("---")
st.sidebar.info("🧪 **Bias Evaluation Tool** v1.0\n\nRuns paired simulations (swapping positions) to measure Position Bias (FAS, BRD, CAS, PANAS).")

# ============================================================================
# PAGE: RUN EXPERIMENT
# ============================================================================
if page == "Run Experiment":
    st.title("🧪 Run New Experiment")
    st.markdown("Configure and run a paired experiment to evaluate position bias.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Configuration")
        
        # Structure (Top)
        structure_options = ["LLM-Based Selection", "Sequential"]
        conversation_structure = st.selectbox("Conversation Structure", structure_options, index=0)
        
        # Trigger is no longer used, so we default to Control
        selected_trigger = "Control"

        selected_topic = st.selectbox("Topic", topics, index=0)
        
        enable_goals = st.checkbox("Include Therapeutic Goals", value=True, help="If unchecked, the specific short and long term goals will be omitted from generation.")
        
        turn_count = st.number_input("Total Simulation Turns", min_value=5, max_value=100, value=30, help="Total number of dialog turns (including Therapist and AI Facilitator)")

        temperature = st.slider("Temperature (Creativity)", min_value=0.0, max_value=1.5, value=0.7, step=0.1)

        enable_progress = st.radio(
            "Session Progress Arc",
            ["Disabled", "Enabled"],
            index=0,
            help="When enabled, patients receive a phase signal (Early / Middle / Late / Closing) based on how far through the session they are, preventing looping on the same complaint."
        ) == "Enabled"

        therapist_mode = "individual_focus" if st.radio(
            "Therapist Mode",
            ["Standard", "Individual Focus"],
            index=0,
            help="Standard: therapist addresses both partners per turn. Individual Focus: therapist addresses ONE partner per turn — chosen by the model."
        ) == "Individual Focus" else "standard"

        from config import THERAPIST_MODEL_OPTIONS
        therapist_model = st.selectbox(
            "Therapist Model",
            options=list(THERAPIST_MODEL_OPTIONS.keys()),
            index=0,
            help="GPT-4o uses OpenAI. Llama/Gemma options use OpenRouter (free test tier — swap to paid models for full experiment)."
        )
        therapist_model = THERAPIST_MODEL_OPTIONS[therapist_model]

        swap_mode = st.radio(
            "Swap Mode",
            ["Position Swap", "Persona Swap"],
            index=0,
            help="Position Swap: same persona stays in same slot (A/B), only speaking order changes. "
                 "Persona Swap: personas swap slots AND speaking order — Run 2 puts the original Patient B persona into the Patient A slot (with its 'most directly affected' prompt) and vice versa."
        )

        # Persona Selection — independent bid_style filter per patient
        all_personas = assets["personas"]
        bid_style_options = ["All", "assertive", "passive", "aggressive"]
        bid_style_labels = {
            "All": "All Styles",
            "assertive": "Assertive (Turning Toward)",
            "passive": "Passive (Turning Away)",
            "aggressive": "Aggressive (Turning Against)"
        }

        # Patient A
        bid_style_a = st.selectbox(
            "Patient A — Emotional Bid Style",
            bid_style_options,
            format_func=lambda x: bid_style_labels[x],
            index=0,
            key="bid_a",
            help="Filter Patient A personas by Gottman bid response style."
        )
        filtered_a = list(all_personas.keys()) if bid_style_a == "All" else [
            n for n, p in all_personas.items() if p.get("bid_style", "") == bid_style_a
        ]
        if not filtered_a:
            filtered_a = list(all_personas.keys())
        p_a_default = next((n for n in ["Marcus Thompson", "Nathan Pierce", "Victoria Hayes"] if n in filtered_a), filtered_a[0])
        patient_a = st.selectbox("Patient A (Persona)", filtered_a, index=filtered_a.index(p_a_default))

        # Patient B
        bid_style_b = st.selectbox(
            "Patient B — Emotional Bid Style",
            bid_style_options,
            format_func=lambda x: bid_style_labels[x],
            index=0,
            key="bid_b",
            help="Filter Patient B personas by Gottman bid response style."
        )
        filtered_b = list(all_personas.keys()) if bid_style_b == "All" else [
            n for n, p in all_personas.items() if p.get("bid_style", "") == bid_style_b
        ]
        if not filtered_b:
            filtered_b = list(all_personas.keys())
        p_b_default = next((n for n in ["Rachel Kim", "Sophie Chen", "Kevin Murphy"] if n in filtered_b and n != patient_a), filtered_b[0])
        patient_b = st.selectbox("Patient B (Persona)", filtered_b, index=filtered_b.index(p_b_default))

    with col2:
        st.subheader("2. Experiment Plan")
        if swap_mode == "Position Swap":
            st.info(f"""
            **Mode: Position Swap**

            1. **Run 1:** {patient_a} (Slot A) speaks first.
            2. **Run 2:** {patient_b} (Slot B) speaks first. Slots unchanged.

            Same persona keeps same prompt (A="most affected", B="equally invested").
            Only speaking order changes.
            """)
        else:
            st.info(f"""
            **Mode: Persona Swap**

            1. **Run 1:** {patient_a} = Slot A (speaks first), {patient_b} = Slot B.
            2. **Run 2:** {patient_b} = Slot A (speaks first), {patient_a} = Slot B.

            Personas swap slots AND prompts. FAS/BRD/CAS scores for Run 2
            will be flipped so positive always = "{patient_a}-aligned".
            """)
        
        if st.button("🚀 Start Experiment Pair", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # --- RUN 1 (A First) ---
                status_text.text(f"Running Simulation 1/2: {patient_a} starts...")
                progress_bar.progress(10)
                
                desc_1 = f"UI Run (A-First): {selected_trigger} - {patient_a} vs {patient_b}"
                
                st.markdown(f"#### Live Stream: Run 1 ({patient_a} First)")
                stream_container_1 = st.empty()
                current_stream_1 = []

                def append_to_stream_1(speaker, text, emotion_label=None, trajectory=None):
                    emotion_badge = ""
                    if emotion_label:
                        trajectory_icon = {"escalating": "↑", "de-escalating": "↓", "stable": "→"}.get(trajectory, "")
                        emotion_badge = f" `{emotion_label}` {trajectory_icon}"
                    if speaker in ["Therapist", "AI Facilitator"]:
                        formatted_text = f"**{speaker}**: {text}"
                    elif patient_a in speaker:
                        formatted_text = f"🟡 **{speaker}**{emotion_badge}: {text}"
                    else:
                        formatted_text = f"🟢 **{speaker}**{emotion_badge}: {text}"
                    current_stream_1.append(formatted_text)
                    stream_container_1.info("\n\n".join(current_stream_1))

                t1_path = run_single_experiment(
                    assets=assets,
                    structure=conversation_structure,
                    first_speaker="Patient A First",  # A is first
                    description=desc_1,
                    patient_a_name=patient_a,
                    patient_b_name=patient_b,
                    topic_name=selected_topic,
                    turn_limit=turn_count,
                    temperature=temperature,
                    turn_callback=append_to_stream_1,
                    enable_goals=enable_goals,
                    enable_progress=enable_progress,
                    therapist_mode=therapist_mode,
                    therapist_model=therapist_model
                )
                progress_bar.progress(50)
                st.success(f"Run 1 Complete: {os.path.basename(t1_path)}")
                
                # --- RUN 2 ---
                # Determine Run 2 parameters based on swap mode
                if swap_mode == "Persona Swap":
                    # Swap slots: original B becomes slot A, original A becomes slot B
                    r2_patient_a = patient_b  # original B now in slot A
                    r2_patient_b = patient_a  # original A now in slot B
                    r2_first_speaker = "Patient A First"  # slot A speaks first (= original B)
                    r2_desc = f"UI Run (Persona Swap): {patient_b} as Slot A vs {patient_a} as Slot B"
                    r2_label = f"{patient_b} First (Swapped Slots)"
                else:
                    # Only position swap: same slots, B speaks first
                    r2_patient_a = patient_a
                    r2_patient_b = patient_b
                    r2_first_speaker = "Patient B First"
                    r2_desc = f"UI Run (B-First): {selected_trigger} - {patient_a} vs {patient_b}"
                    r2_label = f"{patient_b} First"

                status_text.text(f"Running Simulation 2/2: {r2_label}...")

                st.markdown(f"#### Live Stream: Run 2 ({r2_label})")
                stream_container_2 = st.empty()
                current_stream_2 = []

                def append_to_stream_2(speaker, text, emotion_label=None, trajectory=None):
                    emotion_badge = ""
                    if emotion_label:
                        trajectory_icon = {"escalating": "↑", "de-escalating": "↓", "stable": "→"}.get(trajectory, "")
                        emotion_badge = f" `{emotion_label}` {trajectory_icon}"
                    if speaker in ["Therapist", "AI Facilitator"]:
                        formatted_text = f"**{speaker}**: {text}"
                    elif patient_a in speaker:
                        formatted_text = f"🟡 **{speaker}**{emotion_badge}: {text}"
                    else:
                        formatted_text = f"🟢 **{speaker}**{emotion_badge}: {text}"
                    current_stream_2.append(formatted_text)
                    stream_container_2.success("\n\n".join(current_stream_2))

                t2_path = run_single_experiment(
                    assets=assets,
                    structure=conversation_structure,
                    first_speaker=r2_first_speaker,
                    description=r2_desc,
                    patient_a_name=r2_patient_a,
                    patient_b_name=r2_patient_b,
                    topic_name=selected_topic,
                    turn_limit=turn_count,
                    temperature=temperature,
                    turn_callback=append_to_stream_2,
                    enable_goals=enable_goals,
                    enable_progress=enable_progress,
                    therapist_mode=therapist_mode,
                    therapist_model=therapist_model
                )
                progress_bar.progress(90)
                st.success(f"Run 2 Complete: {os.path.basename(t2_path)}")

                # --- EVALUATION ---
                status_text.text("Evaluating Position Bias...")
                is_swapped = (swap_mode == "Persona Swap")
                report = generate_evaluation_report(
                    t1_path, t2_path, threshold=1, slots_swapped=is_swapped
                )

                # Save to DB
                add_experiment_result(
                    selected_trigger, turn_count, patient_a, patient_b,
                    str(t1_path), str(t2_path), report, structure=conversation_structure,
                    swap_mode=swap_mode
                )
                
                progress_bar.progress(100)
                status_text.text("Experiment Complete!")
                st.balloons()
                
                st.divider()
                st.subheader("📝 Immediate Results")
                with st.expander("View JSON Report"):
                    st.json(report)

            except Exception as e:
                st.error(f"Experiment Failed: {e}")
                st.exception(e)

# ============================================================================
# PAGE: COMPARE TRANSCRIPTS
# ============================================================================
elif page == "Compare Transcripts":
    st.title("⚖️ Compare Transcripts")
    st.markdown("Upload two existing transcripts (JSON) to evaluate Position Bias. Parameters must match.")

    compare_swap_mode = st.radio(
        "Were these transcripts generated with Persona Swap?",
        ["No (Position Swap)", "Yes (Persona Swap)"],
        index=0,
        key="compare_swap_mode",
        help="If Persona Swap was used, personas swapped slots in Transcript 2 — names will be in opposite Patient A/B slots."
    )
    compare_is_swapped = (compare_swap_mode == "Yes (Persona Swap)")

    f1 = st.file_uploader("Upload Transcript 1 (Before Swapped)", type="json", key="f1")
    f2 = st.file_uploader("Upload Transcript 2 (After Swapped)", type="json", key="f2")

    if f1 and f2:
        try:
            t1 = json.load(f1)
            f1.seek(0) # Reset stream
            t2 = json.load(f2)
            f2.seek(0)

            # --- Validation ---
            st.subheader("Validation")
            errors = []

            # Check Structure
            if t1.get("conversation_structure") != t2.get("conversation_structure"):
                errors.append(f"Structure mismatch: '{t1.get('conversation_structure')}' vs '{t2.get('conversation_structure')}'")

            # Check Topic
            if t1.get("session_topic_header") != t2.get("session_topic_header"):
                errors.append(f"Topic mismatch: '{t1.get('session_topic_header')}' vs '{t2.get('session_topic_header')}'")

            # Check Participants (Names)
            pa1 = t1.get("participant_details", {}).get("patient_A", {}).get("name")
            pb1 = t1.get("participant_details", {}).get("patient_B", {}).get("name")
            pa2 = t2.get("participant_details", {}).get("patient_A", {}).get("name")
            pb2 = t2.get("participant_details", {}).get("patient_B", {}).get("name")

            if compare_is_swapped:
                # In Persona Swap mode, T2 has names in opposite slots
                if pa1 != pb2 or pb1 != pa2:
                    errors.append(f"Participant swap mismatch: T1=({pa1}, {pb1}), T2=({pa2}, {pb2}). Expected T2=({pb1}, {pa1}).")
            else:
                if pa1 != pa2 or pb1 != pb2:
                    errors.append(f"Participant mismatch: ({pa1}, {pb1}) vs ({pa2}, {pb2})")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                st.success("✅ Parameters Match! Ready to compare.")
                
                if st.button("Run Comparison Analysis", type="primary"):
                    with st.spinner("Analyzing..."):
                        # Save temp files for evaluate_bias.py
                        temp_dir = "temp_uploads"
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        p1 = os.path.join(temp_dir, f1.name)
                        p2 = os.path.join(temp_dir, f2.name)
                        
                        # Save content
                        with open(p1, "w", encoding='utf-8') as f:
                            json.dump(t1, f, indent=2)
                        with open(p2, "w", encoding='utf-8') as f:
                            json.dump(t2, f, indent=2)
                            
                        # Run Evaluation
                        report = generate_evaluation_report(
                            p1, p2, threshold=1, slots_swapped=compare_is_swapped
                        )

                        # Save to DB
                        trigger = t1.get("participant_details", {}).get("selected_trigger_type", "Unknown")
                        turns = t1.get("session_transcript", [])[-1].get("turn", 0) if t1.get("session_transcript") else 0

                        structure = t1.get("conversation_structure", "Unknown")
                        cmp_swap_label = "Persona Swap" if compare_is_swapped else "Position Swap"
                        add_experiment_result(
                            trigger, turns, pa1, pb1,
                            p1, p2, report, structure=structure,
                            swap_mode=cmp_swap_label
                        )
                        
                        st.balloons()
                        
                        st.divider()
                        st.subheader("📝 Comparison Results")
                        with st.expander("View JSON Report"):
                            st.json(report)

        except Exception as e:
            st.error(f"Error reading files: {e}")


# ============================================================================
# PAGE: RESULTS DASHBOARD
# ============================================================================
elif page == "Results Dashboard":
    st.title("📊 Results Dashboard")
    
    # Load Data
    df = get_all_experiments()
    
    if df.empty:
        st.warning("No experiments found. Go to 'Run Experiment' to create some data.")
    else:
        # Filters
        st.sidebar.subheader("Filters")
        if "structure" in df.columns:
            structures = st.sidebar.multiselect("Structure", df["structure"].unique(), default=df["structure"].unique())
            df_filtered = df[df["structure"].isin(structures)] 
        
        if "trigger_type" in df.columns:
            triggers = st.sidebar.multiselect("Trigger Type", df["trigger_type"].unique(), default=df["trigger_type"].unique())
            filtered_df = df_filtered[df_filtered["trigger_type"].isin(triggers)].copy() if "structure" in df.columns else df[df["trigger_type"].isin(triggers)].copy()
        else:
            filtered_df = df.copy()

        st.sidebar.divider()
        st.sidebar.subheader("Danger Zone")
        if st.sidebar.button("🗑️ Clear All Data", type="primary"):
            clear_all_experiments()
            st.rerun()

        # Prepare Data for Display (Exploding Rows)
        display_rows = []
        
        for index, row in filtered_df.iterrows():
            t1 = row['t1_path']
            t2 = row['t2_path']
            
            s_struct = get_structure_from_file(t1) # Should be same for both
            
            # --- ROW 1 (Transcript 1 - Patient A First) ---
            a1_pos, a1_neg, a1_net = calculate_panas_shift(t1, "Patient_A")
            b1_pos, b1_neg, b1_net = calculate_panas_shift(t1, "Patient_B")
            ta1_val, ta1_neu, ta1_gui, ta1_ovr = get_alliance_scores(t1)
            fas1, brd1, cas1 = get_balance_scores(t1)

            display_rows.append({
                "ID": row['id'],
                "Run": "Run 1",
                "Timestamp": row['timestamp'],
                "Transcript": os.path.basename(t1),
                "Structure": s_struct,
                "Trigger Type": row.get('trigger_type', ''),
                "Patient A": row['patient_a'],
                "Patient B": row['patient_b'],
                "PA Pos": a1_pos, "PA Neg": a1_neg, "PA Net": a1_net,
                "PB Pos": b1_pos, "PB Neg": b1_neg, "PB Net": b1_net,
                "TA Val": ta1_val, "TA Neu": ta1_neu, "TA Gui": ta1_gui, "TA Ovr": ta1_ovr,
                "FAS": fas1, "BRD": brd1, "CAS": cas1,
            })

            # --- ROW 2 (Transcript 2 - Swapped) ---
            row_swap_mode = row.get('swap_mode', 'Position Swap')
            is_personality_swap = (row_swap_mode == "Persona Swap")

            if is_personality_swap:
                # In Persona Swap mode, original Patient A is now in slot B in t2,
                # and original Patient B is in slot A. Cross-reference PANAS keys.
                a2_pos, a2_neg, a2_net = calculate_panas_shift(t2, "Patient_B")
                b2_pos, b2_neg, b2_net = calculate_panas_shift(t2, "Patient_A")
            else:
                a2_pos, a2_neg, a2_net = calculate_panas_shift(t2, "Patient_A")
                b2_pos, b2_neg, b2_net = calculate_panas_shift(t2, "Patient_B")

            ta2_val, ta2_neu, ta2_gui, ta2_ovr = get_alliance_scores(t2)
            fas2, brd2, cas2 = get_balance_scores(t2)

            # In Persona Swap mode, negate FAS/BRD/CAS so positive still
            # means "original Patient A-aligned" across both runs.
            if is_personality_swap and fas2 is not None:
                fas2 = -fas2
            if is_personality_swap and brd2 is not None:
                brd2 = -brd2
            if is_personality_swap and cas2 is not None:
                cas2 = -cas2

            display_rows.append({
                "ID": row['id'],
                "Run": "Run 2" + (" (Swapped)" if is_personality_swap else ""),
                "Timestamp": row['timestamp'],
                "Transcript": os.path.basename(t2),
                "Structure": s_struct,
                "Trigger Type": row.get('trigger_type', ''),
                "Patient A": row['patient_a'],
                "Patient B": row['patient_b'],
                "PA Pos": a2_pos, "PA Neg": a2_neg, "PA Net": a2_net,
                "PB Pos": b2_pos, "PB Neg": b2_neg, "PB Net": b2_net,
                "TA Val": ta2_val, "TA Neu": ta2_neu, "TA Gui": ta2_gui, "TA Ovr": ta2_ovr,
                "FAS": fas2, "BRD": brd2, "CAS": cas2,
            })

        display_df = pd.DataFrame(display_rows)

        st.subheader("Overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Experiments", len(filtered_df))
        if not display_df.empty:
            c2.metric("Avg PA Net Shift", f"{display_df['PA Net'].mean():.2f}")
            c3.metric("Avg PB Net Shift", f"{display_df['PB Net'].mean():.2f}")

        # Main Table
        st.subheader("Experiment History")
        
        final_cols = [
            "ID", "Run", "Transcript", "Structure",
            "Patient A", "Patient B",
            "PA Pos", "PA Neg", "PA Net",
            "PB Pos", "PB Neg", "PB Net",
            "TA Val", "TA Neu", "TA Gui", "TA Ovr",
            "FAS", "BRD", "CAS",
        ]
        
        if not display_df.empty:
            st.dataframe(
                display_df[final_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No data to display.")
        
        # Detail View
        st.subheader("Experiment Details")
        exp_ids = filtered_df["id"].tolist()
        if exp_ids:
            selected_id = st.selectbox("Select Experiment ID to View Details", exp_ids)
            
            if selected_id:
                row = filtered_df[filtered_df["id"] == selected_id].iloc[0]
                report = json.loads(row["report_json"])
                
                st.markdown(f"#### Experiment #{selected_id}: {row['patient_a']} vs {row['patient_b']}")
                
                tab1, tab2, tab3 = st.tabs(["Metrics", "Transcript Viewer", "Metadata"])
                
                with tab1:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**Patient A ({row['patient_a']})**")
                        det_a = report["details"][row["patient_a"]]
                        panas_a = det_a.get("panas_summary", {})
                        if panas_a:
                            st.write(f"Net PANAS (first): {panas_a.get('net_first', 'N/A')}")
                            st.write(f"Net PANAS (second): {panas_a.get('net_second', 'N/A')}")

                    with col_b:
                        st.markdown(f"**Patient B ({row['patient_b']})**")
                        det_b = report["details"][row["patient_b"]]
                        panas_b = det_b.get("panas_summary", {})
                        if panas_b:
                            st.write(f"Net PANAS (first): {panas_b.get('net_first', 'N/A')}")
                            st.write(f"Net PANAS (second): {panas_b.get('net_second', 'N/A')}")
                
                with tab2:
                    # Utility to load text content from session transcript
                    def get_transcript_dialogue(path):
                        if os.path.exists(path):
                            try:
                                with open(path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                return data.get('session_transcript', [])
                            except:
                                return []
                        return []

                    t1_turns = get_transcript_dialogue(row['t1_path'])
                    t2_turns = get_transcript_dialogue(row['t2_path'])
                    
                    t_col1, t_col2 = st.columns(2)
                    
                    with t_col1:
                        st.markdown(f"**Run 1: {row['patient_a']} First**")
                        for turn in t1_turns:
                            spk = turn.get('speaker', 'Unknown')
                            txt = turn.get('dialogue', '')
                            if spk == "Therapist":
                                st.info(f"**{spk}**: {txt}")
                            elif spk == row['patient_a']:
                                st.warning(f"**{spk}**: {txt}")
                            else:
                                st.success(f"**{spk}**: {txt}")

                    with t_col2:
                        st.markdown(f"**Run 2: {row['patient_b']} First**")
                        for turn in t2_turns:
                            spk = turn.get('speaker', 'Unknown')
                            txt = turn.get('dialogue', '')
                            if spk == "Therapist":
                                st.info(f"**{spk}**: {txt}")
                            elif spk == row['patient_a']:
                                st.warning(f"**{spk}**: {txt}")
                            else:
                                st.success(f"**{spk}**: {txt}")

                with tab3:
                    st.write(f"**Run 1 Path:** `{row['t1_path']}`")
                    st.write(f"**Run 2 Path:** `{row['t2_path']}`")
                    st.json(report["meta"])
