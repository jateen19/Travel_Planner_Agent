import streamlit as st
import re
from datetime import date
from state.travel_state import TravelState
from orchestrator import run_travel_planning
from utils.pdf_exporter import export_travel_pdf
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Travel Planner", layout="centered")
st.title("✈️ AI Travel Planner")

with st.form("trip_form"):
    origin_country = st.text_input("Origin Country", placeholder="e.g. United States, Canada, United Kingdom")
    destination = st.text_input("Destination", placeholder="e.g. Paris, Tokyo, New York")
    budget_type = st.selectbox("Budget Type", ["budget", "mid-range", "luxury"])
    trip_type = st.selectbox("Type of Trip", ["adventure", "cultural", "romantic", "family", "solo"])
    num_people = st.selectbox("Number of Travelers", [1, 2, 3, 4, 5, "6+"])
    if num_people == "6+":
        num_people = 6
    start_date = st.date_input("Start Date", min_value=date.today())
    end_date = st.date_input("End Date", min_value=start_date)
    additional_comments = st.text_area(
        "Additional Comments",
        placeholder="e.g. I love museums and local food. Avoid long hikes."
    )
    include_activities = st.checkbox("Suggest Activities", help="Get curated activity suggestions organized by category (History, Food, Hidden Gems, etc.)")
    submitted = st.form_submit_button("Generate Itinerary")

if submitted:
    state: TravelState = {
        "origin_country": origin_country,
        "destination": destination,
        "budget_type": budget_type,
        "trip_type": trip_type,
        "num_people": int(num_people),
        "start_date": start_date,
        "end_date": end_date,
        "additional_comments": additional_comments,
        "include_activities": include_activities,
    }

    #st.success("Preferences captured!")
    #st.json(state)  # debug

    with st.spinner("Creating your travel plan..."):
        result = run_travel_planning(state)
        # Store result in session state to persist across button clicks
        st.session_state['travel_result'] = result
        st.session_state['travel_state'] = state

# Check if we have results to display (from current submission or session state)
if 'travel_result' in st.session_state and 'travel_state' in st.session_state:
    result = st.session_state['travel_result']
    state = st.session_state['travel_state']
    
    st.success(" Your travel plan is ready!")
    
    # Display visa information in expandable section
    if "visa_info" in result:
        with st.expander("🛂 Visa Information", expanded=True):
            st.info(result["visa_info"])

    # Display weather forecast in expandable section
    if "weather_forecast" in result:
        with st.expander("🌤️ Weather Forecast", expanded=True):
            st.markdown(result["weather_forecast"])

    # Display itinerary in expandable section
    with st.expander("🧳 Your Travel Itinerary", expanded=True):
        st.markdown(result["itinerary"])

    # Display hotel recommendations in expandable section
    if "suggested_hotels" in result:
        with st.expander("🏨 Hotel Recommendations", expanded=False):
            st.markdown(result["suggested_hotels"])

    # Display activities in expandable section
    if include_activities and "suggested_activities" in result:
        with st.expander("🎯 Suggested Activities", expanded=False):
            st.markdown(result["suggested_activities"])
    
    # PDF Export Section
    st.divider()
    st.subheader("📄 Export Your Travel Plan")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("Download your complete travel plan as a professional PDF document.")
    with col2:
        if st.button("📥 Download PDF", type="primary"):
            try:
                # Generate PDF
                with st.spinner("Generating PDF..."):
                    pdf_bytes = export_travel_pdf(state, result)
                
                # Create filename
                destination_clean = re.sub(r'[^\w\s-]', '', state["destination"]).strip()
                destination_clean = re.sub(r'[-\s]+', '-', destination_clean)
                filename = f"travel-plan-{destination_clean}-{state['start_date'].strftime('%Y%m%d')}.pdf"
                
                # Download button
                st.download_button(
                    label="📁 Save PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    help="Click to save your travel plan as PDF"
                )
                st.success("✅ PDF generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Failed to generate PDF: {str(e)}")
                st.info("💡 Make sure all sections have been generated before exporting.")
